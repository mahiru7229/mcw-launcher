# Apply MCW Launcher v1.5.1 stable

This patch applies on top of the final v1.5.1-beta.7 source.

It promotes the launcher to stable `v1.5.1` and upgrades MCW Update Bridge to v1.6.0, pinned to the stable release.

Recommended release order:

1. Apply this patch and commit.
2. Tag `v1.5.1`.
3. Publish `v1.5.1` as a normal GitHub Release (not pre-release) so `release.yml` builds Windows/Linux launcher packages.
4. After the stable launcher assets are attached, run **Build MCW Update Bridge** with:
   - `release_tag = v1.5.1`
   - `upload_to_release = true`
   - `activate_release_override = false`
5. Verify the stable release contains both launcher ZIPs/checksums and four Bridge v1.6.0 assets.

Do not enable `MCW-USE-BRIDGE` for normal stable publication. Users on v1.5.0 must run Bridge manually once because v1.5.0 predates automatic Bridge routing.
