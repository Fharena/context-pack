# 릴리즈 가이드

현재는 GitHub에서 바로 설치할 수 있습니다. PyPI/npm 배포는 선택 사항이지만, release workflow가 GitHub Release 자산과 registry 배포 준비 상태를 같이 관리합니다.

## 사전 검증

깨끗한 `main` checkout에서 실행합니다.

```bash
git status --short
python scripts/sync_packaged_assets.py --check
python -m unittest discover -s tests -v
python scripts/validate_packaged_cli.py
python -m json.tool plugins/context-pack/.codex-plugin/plugin.json
python -m json.tool .context-pack/manifest.json
python -m json.tool .agents/plugins/marketplace.json
python -m json.tool package.json
python -m pip install build twine
python -m build
python -m twine check dist/*
npm pack --dry-run
node bin/context-pack.js --help
```

## 버전 올리기

다음 파일의 버전을 함께 맞춥니다.

```text
pyproject.toml
package.json
src/context_pack/__init__.py
plugins/context-pack/.codex-plugin/plugin.json
plugins/context-pack/skills/context-pack/scripts/context_pack.py
src/context_pack/bundled/context_pack.py
CHANGELOG.md
```

그다음 `python scripts/sync_packaged_assets.py`를 실행해 package에 포함되는 engine, skill instruction, agent metadata, plugin manifest가 canonical source와 일치하게 만듭니다.

버전 동기화 테스트:

```bash
python -m unittest tests.test_context_pack.ContextPackTests.test_public_versions_stay_in_sync -v
```

## GitHub Release

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main
git push origin vX.Y.Z
gh release create vX.Y.Z --repo Fharena/context-pack --title "vX.Y.Z" --notes-file <notes.md>
```

GitHub Release가 publish되면 `Release` workflow가 실행됩니다. 이 workflow는 tag가 `pyproject.toml`, `package.json` 버전과 맞는지 확인하고, Python wheel/sdist와 npm tarball을 빌드/검증한 뒤 GitHub Release assets로 업로드합니다.

이미 만든 release의 자산을 다시 만들거나 workflow를 재실행해야 한다면:

```bash
gh workflow run release.yml --repo Fharena/context-pack -f tag=vX.Y.Z
```

홍보 전에 `CI`와 `Release` workflow가 모두 통과했는지 확인합니다.

## 선택적 Registry 자동화

Registry 배포는 의도적으로 opt-in입니다. 기본 release workflow는 GitHub Release assets만 빌드하고 업로드합니다.

Trusted Publishing 설정 후 GitHub release마다 자동 publish하고 싶다면 repository variables를 추가합니다.

```text
PUBLISH_PYPI=true
PUBLISH_NPM=true
```

GitHub Actions에서 한 번만 수동 publish하고 싶다면:

```bash
gh workflow run release.yml --repo Fharena/context-pack \
  -f tag=vX.Y.Z \
  -f publish_pypi=true \
  -f publish_npm=true
```

## PyPI

추천 경로는 PyPI Trusted Publishing입니다. 설정값은 다음처럼 맞춥니다.

```text
owner: Fharena
repository: context-pack
workflow: release.yml
environment: pypi
package: context-pack
```

workflow는 `id-token: write` 권한과 `pypa/gh-action-pypi-publish@release/v1`를 사용하므로, publisher 설정이 끝난 뒤에는 PyPI token이 필요 없습니다.

사전 검증 후 수동 업로드도 가능합니다.

```bash
python -m twine upload dist/*
```

배포 후 확인:

```bash
pipx install context-pack
context-pack --help
```

## npm

추천 경로는 package `@fharena/context-pack`에 npm Trusted Publishing을 설정하는 것입니다. npm trusted publisher의 environment는 workflow와 맞춰야 하며, 현재 workflow environment는 `npm`입니다.

workflow는 `id-token: write` 권한을 받고 `npm publish --access public`을 실행합니다. npm Trusted Publishing이 지원되는 package에서는 provenance가 자동으로 붙습니다.

사전 검증 후 수동 배포도 가능합니다.

```bash
npm login
npm publish --access public
```

배포 후 확인:

```bash
npx @fharena/context-pack --help
```

## 메모

- GitHub release tag, `CI`, `Release`가 green이 되기 전에 registry package를 publish하지 않습니다.
- registry에 배포한 뒤에는 README 설치 예시를 registry 경로 우선으로 바꾸고, GitHub 경로는 fallback으로 남깁니다.
- plugin marketplace 배포 방식이 더 성숙하기 전까지 Codex에서는 `context-pack install-codex --activate`를 추천 경로로 유지합니다.
