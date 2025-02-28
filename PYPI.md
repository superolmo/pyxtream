# Update Poetry

```shell
poetry lock
poetry sync
poetry debug resolve
```

# Build docs

```shell
rm -rf docs
poetry run pdoc -n -o docs pyxtream
```

# Generate requirements.txt

```shell
poetry export --without-hashes > requirements.txt
```

# Build PIP Module

```shell
poetry build
```

# Configure PYPI Token

```shell
poetry config pypi-token.pypi <token>
```
```shell
poetry publish -u __token__ -p <token>
```

# Upload to PYPI

References: https://www.digitalocean.com/community/tutorials/how-to-publish-python-packages-to-pypi-using-poetry-on-ubuntu-22-04

```shell
poetry publish
```

# Optional Local Install

python3 -m pip install dist/pyxtream-0.7

# Record TS Video

ffmpeg -y -i "(iptv url)" -c:v copy -c:a copy  -map 0:v -map 0:a -t 00:00:30 "myrecording.ts" >"mylog.log" 2>&1

# Versioning

- Increment the MAJOR version when you make incompatible API changes.
- Increment the MINOR version when you add functionality in a backwards-compatible manner.
- Increment the PATCH version when you make backwards-compatible bug fixes.
