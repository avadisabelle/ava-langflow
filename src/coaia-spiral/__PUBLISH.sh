v=$(npm version patch) && npm publish && git commit . -m v$v && git tag $v && git push --tags
