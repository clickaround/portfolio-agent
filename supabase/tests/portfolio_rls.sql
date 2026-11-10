-- Run after the foundation migration on a disposable DB with two test auth users.
-- Rolls back test fixtures. Never substitute production user data.
BEGIN;

 create temporary table test_users (n integer, uid uuid);
 insert into test_users select row_number() over (), id from auth.users order by id limit 2;
 do $$ begin if (select count(*) from test_users) <> 2 then raise exception 'Need two existing auth users for rollback-only test'; end if; end $$;
 grant select on test_users to authenticated;
 insert into public.projects (id,owner_id,slug,title) select ('00000000-0000-4000-8000-' || lpad(n::text,12,'0'))::uuid,uid,'rls-rollback-test','test' from test_users;
 insert into public.conversations (id,project_id,created_by) select '00000000-0000-4000-9000-000000000001', '00000000-0000-4000-8000-000000000001', uid from test_users where n=1;
 do $$ begin
   begin
     insert into public.conversations (project_id, created_by)
       select '00000000-0000-4000-8000-000000000001', uid from test_users where n=2;
     raise exception 'Mismatched project owner and creator accepted';
   exception when foreign_key_violation then null;
   end;
 end $$;
 insert into public.messages (id,project_id,conversation_id,sequence,author_kind,state,client_request_id) values ('00000000-0000-4000-a000-000000000001','00000000-0000-4000-8000-000000000001','00000000-0000-4000-9000-000000000001',1,'user','completed','00000000-0000-4000-b000-000000000001');
 insert into public.message_parts (project_id,conversation_id,message_id,ordinal,kind,text_content) values ('00000000-0000-4000-8000-000000000001','00000000-0000-4000-9000-000000000001','00000000-0000-4000-a000-000000000001',0,'text','synthetic test');
 update public.conversations set next_message_seq = 2 where id = '00000000-0000-4000-9000-000000000001';
 set local role authenticated;
 select set_config('request.jwt.claim.sub', (select uid::text from test_users where n=1), true);
 do $$ begin if (select count(*) from public.projects) <> 1 or (select count(*) from public.messages) <> 1 or (select count(*) from public.message_parts) <> 1 then raise exception 'Owner cannot read own data'; end if; end $$;
 do $$ declare first_id uuid; second_id uuid; begin
   select public.append_user_message('00000000-0000-4000-9000-000000000001','00000000-0000-4000-b000-000000000002','new message') into first_id;
   select public.append_user_message('00000000-0000-4000-9000-000000000001','00000000-0000-4000-b000-000000000002','new message') into second_id;
   if first_id <> second_id or (select count(*) from public.messages) <> 2 then raise exception 'Idempotency failed'; end if;
   begin
     perform public.append_user_message('00000000-0000-4000-9000-000000000001','00000000-0000-4000-b000-000000000002','different message');
     raise exception 'Conflicting request accepted';
   exception when invalid_parameter_value then null; end;
 end $$;
 select set_config('request.jwt.claim.sub', (select uid::text from test_users where n=2), true);
 do $$ begin if (select count(*) from public.projects) <> 1 or (select count(*) from public.conversations) <> 0 or (select count(*) from public.messages) <> 0 or (select count(*) from public.message_parts) <> 0 then raise exception 'Cross-user data visible'; end if; end $$;
 do $$ begin begin insert into public.messages(project_id,conversation_id,sequence,author_kind,state,client_request_id) values ('00000000-0000-4000-8000-000000000001','00000000-0000-4000-9000-000000000001',2,'assistant','completed',null); raise exception 'Forgery succeeded'; exception when insufficient_privilege then null; end; end $$;
 do $$ begin begin
   perform public.append_user_message('00000000-0000-4000-9000-000000000001','00000000-0000-4000-b000-000000000003','unauthorized');
   raise exception 'Cross-user append succeeded';
 exception when insufficient_privilege then null; end; end $$;
 reset role;

ROLLBACK;
