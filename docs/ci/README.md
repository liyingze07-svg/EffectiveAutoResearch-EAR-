# Offline continuous integration

[offline.yml](offline.yml) is a ready-to-enable GitHub Actions template. It checks
the report, workflow wiring, research engine, rebuttal helpers and shared CLI on
Python 3.10 and 3.12, without model calls or API keys.

It is stored here as a template and **is not an active workflow**. A maintainer
whose GitHub credential permits workflow changes can enable it from the repository root:

```bash
mkdir -p .github/workflows
cp docs/ci/offline.yml .github/workflows/offline.yml
git add .github/workflows/offline.yml
git commit -m "Enable offline checks on Python 3.10 and 3.12"
git push
```

For OAuth credentials, adding workflow files requires the `workflow` scope in
addition to repository write access. The commands in the template can also be
run locally; they depend only on Python's standard library and Git.
