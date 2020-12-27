# alfred-smartthings-py
Alfred  Workflow for new SmartThings API in python for a smaller workflow - only supports switches and scenes at the moment
## Install

* Can be installed from Packal at http://www.packal.org/workflow/smartthings-new-api-workflow
* Can also be downloaded from github as a zip file, unzip the downloaded zip, cd into the zip directory, and create a new zip with all the files in that folder, and then renamed to Smartthings.alfredworkflow
* Or you can use the workflow-build script in the folder, using
```
chmod +x workflow-build
./workflow-build . 
```
* You will need a personal access token from the SmartThings Developer Portal at https://account.smartthings.com/tokens

## API Key

```
st apikey <personal-access-token>
```
This should only be needed once per install or after a reinit

## Device/Scene Update

```
st update
```
This should be needed once at the install, and everytime you add or delete new devices and/or scenes

## Switch Commands

```
st <switch-name> on|off
```
Turns the Switch on or off - clicking switch name autocompletes switch name and waits for command. If both name and command are provided, executes command and notifies upon success

## Scene Commands

```
st <scene-name>
```
Runs the scene - clicking scene name autocompletes scene name and runs the scene and notifies upon success

## Reinitialize

```
st reinit
```
This should only be needed if you ever want to start again for whatever reason - removes all API keys, devices, scenes, etc.

## Update

```
st workflow:update
```
An update notification should show up when an update is available, but if not invoking this should update the workflow to latest version on github
