# 🇪🇺 Eurostat Data Wizard
A webapp to export easily multiple Eurostat datasets.

## User manual
### 1. Lookup
1. Search and select all variables that you find interesting: dataset containing them will be available in the `Data` page.
### 2. Data
1. Choose an Eurostat dataset of interest (or start typing dataset code or title).
2. After loading, you can inspect the dataset and filter indexes, flags and time-span with the controls provided in the sidebar.
3. Every dataset that you inspect, along with your filtering choice, is saved and can be shown in the `Stash` page by ticking the dedicated checkbox. 
4. You can repeat the process starting from _1_ for as many dataset as you like.

### 3. Stash
Stash it's where you can find every dataset that you inspected. The current stash will be reported here and you can _download_ it in a convenient gzipped csv.

### 4. Timeseries
Stash can also be inspected visually here as separated time series. In order to prevent long loading time, a message will inform you if the amount of variables to be plot are too high.

### 5. Correlations
Stash time series how strong is the correlation across countries. In order to prevent long loading time, a message will inform you if the amount of variables to be plot are too high.

# Installation
## Run the app on localhost
This is a [streamlit](https://streamlit.io/)-based app. Requirements are managed with [pipenv](https://pipenv.pypa.io/) (and it is highly suggested to use [pyenv](https://github.com/pyenv/pyenv) to manage python versions). 
Clone the repo and you should be able to run this command:
```
pipenv run streamlit run Home.py
```
Based on your environment configuration, you may required to satisfy some system dependencies in order to execute the app smoothly. Please refer to the [FAQ](#FAQ) section to solve common issues.

## Live demo
This is a memory intensive webapp, so the cloud use is discouraged. Anyway, a best-effort live demo can be found [here](https://eurostat-datawizard-lum4chi.streamlit.app).

# Development
App was developed with [vscode](https://code.visualstudio.com/). Use it to benefit from the `.vscode/settings.json` to configure testing environment.
Install the full dev toolbox with the command:
```
pipenv install --dev
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
