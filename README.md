# Eurostat Data Wizard
A straightforward webapp to export easily multiple Eurostat datasets. You can play with a (resource limited) working version [here](https://eurostat-datawizard.streamlit.app).

# User guide
## Data Import
0. Wait for app to be initialized (this should take quite a lot at first run).
1. Choose an Eurostat dataset of interest (or start typing dataset code or title).
2. After loading, you can inspect the dataset and filter indexes, flags and time-span with the controls provided in the sidebar.
3. When done, you can _download_ the current data snapshot in a convenient gzipped csv. You can _stash_ it for further inspection down the line. 
5. You can repeat the process starting from _1_ for as many dataset as you like.

## Stash
The current stash will be reported here and you can _download_ it too.

# Run the app on localhost
This is a [streamlit](https://streamlit.io/)-based app. Requirements are managed with [pipenv](https://pipenv.pypa.io/). 
Clone the repo (pay attention to have [Git-LFS](https://git-lfs.github.com/) installed) and you should be able to run this command:
```
pipenv run streamlit run Home.py
```
Based on your environment configuration, you may required to satisfy some system dependencies in order to execute the app smoothly. Please refer to the [FAQ](#FAQ) section to solve common issues.

# Development
App was developed with [vscode](https://code.visualstudio.com/). Use it to benefit from the `.vscode/settings.json` to configure testing environment.
Install the full dev toolbox with the command:
```
pipenv install --dev
```

# FAQ
## System requirements
### Git-LFS
This repo provides a cache to speed-up app initialization process. Be sure to support [Git-LFS](https://git-lfs.github.com/) on your system. On a Mac, you can install it using [Homebrew](https://brew.sh/) and this command:
```
brew install git-lfs
```
### Package [eust](https://github.com/rasmuse/eust)
If you find this error:
```
ERROR:: Could not find a local HDF5 installation.
```
and you are on a Mac, install `hdf5` on your system using [Homebrew](https://brew.sh/) and this command:
```
brew install hdf5
```
then add these env vars to your `.zprofile` o directly on your shell:
```
export HDF5_DIR=/opt/homebrew/opt/hdf5
export BLOSC_DIR=/opt/homebrew/opt/c-blosc
```

# Copyright
Copyright (c) the respective contributors, as shown by the AUTHORS file.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
