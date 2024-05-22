# Build docs
rm -rf doc
pdoc pyxtream -o docs

# Build PIP Module
python3 setup.py sdist bdist_wheel

# Upload to PYPI
twine upload dist/pyxtream-0.7*

# Optional Local Install
python3 -m pip install dist/pyxtream-0.7

# Record TS Video
ffmpeg -y -i "(iptv url)" -c:v copy -c:a copy  -map 0:v -map 0:a -t 00:00:30 "myrecording.ts" >"mylog.log" 2>&1

# Versioning

- Increment the MAJOR version when you make incompatible API changes.
- Increment the MINOR version when you add functionality in a backwards-compatible manner.
- Increment the PATCH version when you make backwards-compatible bug fixes.
