# Legal / clean-input rules

This project is tooling for interoperability, preservation research, education and ports of software you are entitled to work with. It is not a game-content mirror.

## Never commit

- commercial ROMs / ISOs / WBFS / RVZ / WAD images;
- firmware or console keys;
- extracted copyrighted game assets;
- proprietary SDKs;
- proprietary compilers/toolchains;
- DRM/authentication secrets;
- patches whose purpose is to bypass access control rather than enable interoperability.

## Prefer

- hashes and revision identifiers instead of original binaries;
- scripts that consume a local user-provided dump;
- clean-room interfaces/runtime reimplementations;
- upstream open-source decomp/recomp projects;
- generated metadata that does not reproduce substantial copyrighted content;
- runtime extraction of user-owned content when legally appropriate.

## Repository design

All generated port workspaces ignore common original-input folders and game-image extensions. Upstream tools are cloned into `.tools/`, not vendored.

Before publishing a specific game port, check the licenses of:

1. the decomp/recomp tool;
2. the runtime;
3. emulator-derived code;
4. libraries linked into the Wasm build;
5. any redistributed patches/data tables.

A technically clean build can still have incompatible redistribution licenses. Treat license review as part of the port.
