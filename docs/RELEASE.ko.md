# 릴리즈 가이드

현재는 GitHub에서 바로 설치할 수 있습니다. PyPI/npm 배포는 선택 사항이지만, 아래 검증을 통과하면 registry에 올릴 준비가 된 상태로 볼 수 있습니다.

## 사전 검증

깨끗한 `main` checkout에서 실행합니다.

```bash
git status --short
context-pack status
python -m unittest discover -s tests -v
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
README.md
README.ko.md
CHANGELOG.md
```

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

홍보 전에 GitHub Actions가 통과했는지 확인합니다.

## PyPI

처음 배포하려면 PyPI API token 또는 이 repo에 대한 Trusted Publishing 설정이 필요합니다.

사전 검증 후 수동 업로드:

```bash
python -m twine upload dist/*
```

배포 후 확인:

```bash
pipx install context-pack
context-pack --help
```

## npm

처음 배포하려면 `@fharena` scope에 권한이 있는 npm 계정이 필요합니다.

사전 검증 후 수동 배포:

```bash
npm login
npm publish --access public
```

배포 후 확인:

```bash
npx @fharena/context-pack --help
```

## 메모

- GitHub release tag와 CI가 green이 되기 전에 registry package를 publish하지 않습니다.
- registry에 배포한 뒤에는 README 설치 예시를 registry 경로 우선으로 바꾸고, GitHub 경로는 fallback으로 남깁니다.
- plugin marketplace 배포 방식이 더 성숙하기 전까지 Codex에서는 `context-pack install-codex --activate`를 추천 경로로 유지합니다.
