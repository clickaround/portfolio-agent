# HarnessRouter/UHP scope

- Source: https://github.com/HarnessRouter/harnessrouter; UHP reference protocol/API, sessions, file input/output, conformance, skills/plugins, runtime management; **does not score design quality**.
- A local Codex/Claude plugin requires neither HarnessRouter server nor UHP. Direct host is first runtime.
- Candidate future use: execute same fixture across different Harness+model with trace/cost/session/file recovery, if quantified value justifies added infra.
- Security/ops: API and provider keys separate, keep loopback local during spike, confine upload/project files, redaction of secrets, no broad filesystem access, pin image version, record Docker/storage/network.
- Commercial license: core Community Edition Apache-2.0; **starter-kit/kits/slides is separately licensed**. Do not copy that kit into sellable product without a suitable license. The tool's quickstart may require Docker, disk, and provider API key; do not install without permission.
- Tests: UHP conformance covers API behavior and plugin package transport, not A3 PDF fidelity or professional aesthetic quality. Run own portfolio eval separately.
