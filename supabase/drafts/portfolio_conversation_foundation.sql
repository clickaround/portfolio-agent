-- Foundation only. Does not migrate the existing filesystem projects or
-- persist assistant output. Do not deploy until the API and RLS tests exist.
create table public.projects (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id),
    slug text not null check (slug ~ '^[a-z0-9][a-z0-9_-]{0,63}$'),
    title text not null check (length(title) between 1 and 200),
    brief text not null default '',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz,
    unique (owner_id, slug),
    unique (id, owner_id)
);

create index projects_owner_updated_idx on public.projects (owner_id, updated_at desc, id);

create table public.conversations (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null,
    created_by uuid not null references auth.users(id),
    title text not null default '' check (length(title) <= 200),
    next_message_seq bigint not null default 1 check (next_message_seq > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    archived_at timestamptz,
    unique (project_id, id),
    foreign key (project_id, created_by) references public.projects(id, owner_id)
);

create index conversations_project_updated_idx on public.conversations (project_id, updated_at desc, id);

create table public.messages (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null,
    conversation_id uuid not null,
    sequence bigint not null check (sequence > 0),
    author_kind text not null check (author_kind in ('user', 'assistant', 'system', 'tool')),
    state text not null check (state in ('pending', 'streaming', 'completed', 'failed', 'cancelled', 'unknown_outcome')),
    client_request_id uuid,
    created_at timestamptz not null default now(),
    foreign key (project_id, conversation_id) references public.conversations(project_id, id),
    unique (project_id, conversation_id, id),
    unique (conversation_id, sequence),
    unique (conversation_id, client_request_id),
    check (author_kind <> 'user' or client_request_id is not null)
);

create table public.message_parts (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null,
    conversation_id uuid not null,
    message_id uuid not null,
    ordinal integer not null check (ordinal >= 0),
    kind text not null check (kind = 'text'),
    text_content text not null check (length(text_content) between 1 and 6000),
    schema_version integer not null default 1 check (schema_version = 1),
    foreign key (project_id, conversation_id, message_id) references public.messages(project_id, conversation_id, id),
    unique (message_id, ordinal)
);

create table public.agent_runs (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null,
    conversation_id uuid not null,
    request_message_id uuid not null,
    status text not null default 'queued' check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled', 'unknown_outcome')),
    created_at timestamptz not null default now(),
    foreign key (project_id, conversation_id, request_message_id) references public.messages(project_id, conversation_id, id),
    unique (project_id, conversation_id, id),
    unique (conversation_id, request_message_id)
);

create unique index one_active_run_per_conversation on public.agent_runs(conversation_id)
    where status in ('queued', 'running');

create table public.run_attempts (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null,
    conversation_id uuid not null,
    run_id uuid not null,
    attempt_no integer not null check (attempt_no > 0),
    status text not null default 'queued' check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled', 'unknown_outcome')),
    created_at timestamptz not null default now(),
    foreign key (project_id, conversation_id, run_id) references public.agent_runs(project_id, conversation_id, id),
    unique (project_id, conversation_id, run_id, id),
    unique (run_id, attempt_no)
);

-- Outbox rows are not exposed to client roles. A future worker must claim
-- and dispatch these with a lease and guard against duplicate side effects.
create table public.run_outbox (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null,
    conversation_id uuid not null,
    run_id uuid not null,
    attempt_id uuid not null,
    created_at timestamptz not null default now(),
    foreign key (project_id, conversation_id, run_id, attempt_id) references public.run_attempts(project_id, conversation_id, run_id, id),
    unique (attempt_id)
);

-- Expose read-only rows to owners. Direct table writes stay server-only;
-- authenticated user-message writes go through the restricted function below.
alter table public.projects enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.message_parts enable row level security;
alter table public.agent_runs enable row level security;
alter table public.run_attempts enable row level security;
alter table public.run_outbox enable row level security;

revoke all on public.projects, public.conversations, public.messages, public.message_parts, public.agent_runs, public.run_attempts, public.run_outbox from public, anon, authenticated;
grant select on public.projects, public.conversations, public.messages, public.message_parts, public.agent_runs, public.run_attempts to authenticated;

create policy projects_read_owner on public.projects for select to authenticated
    using (owner_id = (select auth.uid()) and deleted_at is null);
create policy conversations_read_owner on public.conversations for select to authenticated
    using (exists (select 1 from public.projects p where p.id = project_id and p.owner_id = (select auth.uid()) and p.deleted_at is null));
create policy messages_read_owner on public.messages for select to authenticated
    using (exists (select 1 from public.projects p where p.id = project_id and p.owner_id = (select auth.uid()) and p.deleted_at is null));
create policy message_parts_read_owner on public.message_parts for select to authenticated
    using (exists (select 1 from public.projects p where p.id = project_id and p.owner_id = (select auth.uid()) and p.deleted_at is null));
create policy agent_runs_read_owner on public.agent_runs for select to authenticated
    using (exists (select 1 from public.projects p where p.id = project_id and p.owner_id = (select auth.uid()) and p.deleted_at is null));
create policy run_attempts_read_owner on public.run_attempts for select to authenticated
    using (exists (select 1 from public.projects p where p.id = project_id and p.owner_id = (select auth.uid()) and p.deleted_at is null));

-- The trusted function owns all user-message writes. It checks the caller and
-- locks the conversation before allocating a sequence or checking a retry.
create function public.append_user_message(p_conversation_id uuid, p_request_id uuid, p_text text)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog
as $$
declare
    v_project_id uuid;
    v_sequence bigint;
    v_existing_id uuid;
    v_existing_text text;
    v_message_id uuid;
    v_run_id uuid;
    v_attempt_id uuid;
begin
    if auth.uid() is null or p_conversation_id is null or p_request_id is null
       or p_text is null or length(trim(p_text)) = 0 or length(p_text) > 4000 then
        raise exception 'Invalid message request' using errcode = '22023';
    end if;
    select c.project_id, c.next_message_seq into v_project_id, v_sequence
      from public.conversations c join public.projects p on p.id = c.project_id
     where c.id = p_conversation_id and p.owner_id = auth.uid() and p.deleted_at is null and c.archived_at is null
       for update of c;
    if not found then
        raise exception 'Conversation unavailable' using errcode = '42501';
    end if;
    select m.id, mp.text_content into v_existing_id, v_existing_text
      from public.messages m join public.message_parts mp on mp.message_id = m.id and mp.ordinal = 0
     where m.conversation_id = p_conversation_id and m.client_request_id = p_request_id;
    if found then
        if v_existing_text is distinct from p_text then
            raise exception 'Request ID already used with different content' using errcode = '22023';
        end if;
        return v_existing_id;
    end if;
    if exists (select 1 from public.agent_runs r where r.conversation_id = p_conversation_id and r.status in ('queued', 'running')) then
        raise exception 'Conversation already has an active run' using errcode = '55000';
    end if;
    insert into public.messages(project_id, conversation_id, sequence, author_kind, state, client_request_id)
      values (v_project_id, p_conversation_id, v_sequence, 'user', 'completed', p_request_id)
      returning id into v_message_id;
    insert into public.message_parts(project_id, conversation_id, message_id, ordinal, kind, text_content)
      values (v_project_id, p_conversation_id, v_message_id, 0, 'text', p_text);
    insert into public.agent_runs(project_id, conversation_id, request_message_id)
      values (v_project_id, p_conversation_id, v_message_id) returning id into v_run_id;
    insert into public.run_attempts(project_id, conversation_id, run_id, attempt_no)
      values (v_project_id, p_conversation_id, v_run_id, 1) returning id into v_attempt_id;
    insert into public.run_outbox(project_id, conversation_id, run_id, attempt_id)
      values (v_project_id, p_conversation_id, v_run_id, v_attempt_id);
    update public.conversations set next_message_seq = v_sequence + 1, updated_at = now() where id = p_conversation_id;
    return v_message_id;
end;
$$;
revoke all on function public.append_user_message(uuid, uuid, text) from public, anon, authenticated;
grant execute on function public.append_user_message(uuid, uuid, text) to authenticated;
