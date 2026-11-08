# Pascal editor source

`designcraft/` is our editable source copy of [DesignCraft](https://github.com/storytold/designcraft) at `a4017a3cda704850fcb6ed9f8513fdb2e7fb04c1` (v0.17.0). It is copyright the upstream contributors and dual MIT/Apache-2.0; its license files, NOTICE, and asset attributions are retained in that directory. Upstream `docs/brand/` trademark files are not included. Bundled third-party font and other notices remain applicable.

The workbench integration in `apps/designcraft-web/src/pascal_bridge.rs` and `web.rs` adds a same-origin parent message interface with an explicit edit-command allowlist. The interface does not permit file/network commands. The Book page can ask the text-only agent to rewrite explicitly supplied text, let the user choose the proposal, and insert it into a new frame. This is an initial integration, not InDesign feature parity or automatic AI layout. An opened document still needs explicit save and import back into the portfolio project.

Build from `editor/designcraft/apps/designcraft-web` using Rust 1.95, target `wasm32-unknown-unknown`, a native C/C++ build toolchain and Trunk 0.22.1:

```sh
trunk build --release
python ../../../../project/scripts/install_pascal_editor.py
```

On Windows initialize the Visual Studio C++ build environment first and stop any frontend development server before replacing an existing editor build. Cargo resolves pinned git revisions and the versions in `Cargo.lock`; the first build downloads and compiles dependencies. The installer publishes the resulting build and license notices to `frontend/public/pascal-editor/` and refuses to replace a directory it did not create. The original official editor installer remains available separately.
