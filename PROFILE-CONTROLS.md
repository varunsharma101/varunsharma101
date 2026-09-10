# Profile visibility

[Open the profile visibility control](https://github.com/varunsharma101/varunsharma101/actions/workflows/profile-visibility.yml).

Choose **Run workflow**, choose **on** or **off**, then **Run workflow**.

- **on** displays the full README on your GitHub profile.
- **off** hides the custom README while leaving GitHub's normal profile, pinned repositories, and contribution calendar visible.

The workflow renames `README.md` to `PROFILE.md` when off and renames it back when on. It preserves the complete contents and Git history. It does not delete the repository, change repository visibility, or change anyone's theme settings. The change affects all visitors, and normally takes a few seconds after the workflow finishes.

When the view is off, edit `PROFILE.md` to update the saved profile. The daily contribution graphics continue refreshing in the background.
