# Eurostat Data Wizard
A straightforward webapp to export easily multiple Eurostat datasets. You can play with a (**resource limited**) working version [here](https://eurostat-datawizard.streamlit.app).

⚠️ For a better experience, cloning the repo and run it locally is highly suggested! ⚠️

# User guide
## Home [Optional]
1. In order to gain advanced variable search, app must create an index for Eurostat data. This step requires a considerable amount of time but should be done just once. 
2. While running, do not leave or refresh page. If connection is reset for some reason, you can resume index creation: previous API requests are cached and will be faster to process.
3. When ready, index is persisted on disk and all app users can benefit from it. Bear in mind that index can become too old but it can be refreshed. Check the displayed date to guide your choice.

## Map [Optional]
An overview of every Eurostat dataset, characterized by its variables, in relation with each other. Closer the datasets, more the variable shared among them. Map is available only if an index was created. Clusters are shown as a Plotly scatterplot, you can take advantage of its interactive ability:
1. Zoom in/out section of the map by drawing box around datapoints.
2. Toggle datapoint visibility double-clicking on corresponding legend label.

## Data
1. [Optional] Filter Eurostat datasets list by a variable of interest OR by selected datasets in the `Map` page. These options appears only if an index and a clustering were created, respectively.
2. Choose an Eurostat dataset of interest (or start typing dataset code or title).
3. After loading, you can inspect the dataset and filter indexes, flags and time-span with the controls provided in the sidebar.
4. Every dataset that you inspect, along with your filtering choice, is saved and can be shown in the `Stash` page by ticking the dedicated checkbox. 
5. You can repeat the process starting from _1_ for as many dataset as you like.

## Stash
Stash it's where you can find every dataset that you inspected. The current stash will be reported here and you can _download_ it in a convenient gzipped csv.

## Plot
Stash can also be inspected visually here as separated time series. In order to prevent long loading time, a message will inform you if the amount of variables to be plot are too high.

# Run the app on localhost
This is a [streamlit](https://streamlit.io/)-based app. Requirements are managed with [pipenv](https://pipenv.pypa.io/). 
Clone the repo and you should be able to run this command:
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
