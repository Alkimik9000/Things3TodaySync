# Things URL Scheme Reference

This file summarizes the Things URL scheme based on the official documentation at <https://culturedcode.com/things/support/articles/2803573/>.

Use these commands to construct links that automate task creation, search, and navigation in Things.

## Contents

1. [Link Builder](#link-builder)
2. [Overview](#overview)
3. [Commands](#commands)
   - [add](#add)
   - [add-project](#add-project)
   - [update](#update)
   - [update-project](#update-project)
   - [show](#show)
   - [search](#search)
   - [version](#version)
4. [For Developers](#for-developers)
   - [json](#json)
   - [add-json (deprecated)](#add-json-deprecated)

## Link Builder

Use the [online tool](https://culturedcode.com/things/support/articles/2803573/#link-builder) to quickly craft URLs. Fill in fields and copy the generated link.

## Overview

Every command starts with `things:///commandName` followed by optional parameters:

```text
things:///commandName?parameter1=value1&parameter2=value2
```

Opening the link launches Things and performs the action. All commands support the x-callback-url convention (`x-success`, `x-error`, `x-cancel`).

To obtain IDs of to‑dos or lists, copy their Things links via the Share menu.

## Commands

### add

Create one or more to-dos.

Example adding a single to-do:

```text
things:///add?title=Buy%20milk
```

Parameters include:

- `title` or `titles`
- `notes`
- `when` (e.g. `today`, `tomorrow`, `yyyy-mm-dd`)
- `deadline`
- `tags`
- `checklist-items`
- `list` or `list-id`
- `heading` or `heading-id`
- `completed` / `canceled`
- `show-quick-entry`
- `reveal`

`when` accepts natural language like `next tuesday` and scheduling with `evening@6pm` sets a reminder.

### add-project

Create a project and optional to-dos within it.

```text
things:///add-project?title=Build%20treehouse&when=today
```

Parameters mirror those of `add` plus project specific ones such as `area` or `area-id`, `to-dos`, `completed`, `canceled`, and `reveal`.

### update

Modify an existing to-do. Requires `id` and `auth-token`.

```text
things:///update?id=4BE64FEA-8FEF-4F4F-B8B2-4E74605D5FA5&when=today
```

Include any of the `add` parameters to change them. Setting a parameter to an empty value clears it (e.g. `deadline=`).

### update-project

Modify an existing project. Requires `id` and `auth-token`.

```text
things:///update-project?id=852763FD-5954-4DF9-A88A-2ADD808BD279&when=tomorrow
```

### show

Navigate to a list, project, area, tag, or to-do.

```text
things:///show?id=today
```

If you pass `query`, Things opens the first Quick Find result. Optionally filter by tags using `filter`.

### search

Open the Things search screen. Provide `query` to prefill the search field.

### version

Return the Things client and URL scheme version via x-callback parameters.

## For Developers

### json

A JSON-based command that can create entire projects with nested to-dos. Build a JSON array describing the items, remove whitespace, URL encode it, then pass as the `data` parameter:

```text
things:///json?data=%5B%7B%22type%22:%22to-do%22,%22attributes%22:%7B%22title%22:%22Buy%20milk%22%7D%7D%5D
```

Authentication (`auth-token`) is required when performing updates.

### add-json (deprecated)

Replaced by `json`.

## Data Types

Parameter values may be strings, dates (`yyyy-mm-dd`), booleans, or JSON. Relative dates like `today`, `tomorrow`, or `in 3 days` are accepted. Time strings such as `21:30` can be combined with a date using `@` (e.g. `2025-06-14@09:00`).

## Enabling the URL Scheme

The first time you open a Things URL, the app asks to enable the scheme. You can manage this under **Settings → General → Things URLs**.

## Version

Current scheme version: **2**.

---

This is a condensed copy of the official documentation. See the [original article](https://culturedcode.com/things/support/articles/2803573/) for full details.



-------- The Original Content -------- 
Clip source: Things URL Scheme - Things Support


			 						Things URL Scheme 					

The URL scheme lets pro users and developers of other apps send commands to Things. This page explains how it works.
Here are some examples of commands that Things understands:
- Create a new to-do named “Buy milk”.
- Show the Today list.
- Show all to-dos tagged with “Errand”.
- Search all to-dos for “shipping address”.
There’s also a powerful JSON-based command that lets you create entire projects, together with all their notes, headings, and to-dos.

In this article:

1. Link Builder
2. Overview
3. Commands
	- add
	- add-project
	- update
	- update-project
	- show
	- search
	- version
4. For Developers
	- json
	- add-json (deprecated)

Link Builder

You can find the full documentation for each supported command further below. If you want to jump right in, here’s a little link builder tool to get you started. Simply fill out some of the fields and the corresponding link will be created for you on the fly. Enjoy!
addadd-projectupdateupdate-projectshowsearchjson

	things:///add?

title /  						titles

completed  						or  						canceledshow-quick-entryreveal

notes

checklist-items

when

deadline

tags

list /  						list-id

heading

creation-date

completion-date


Overview

Commands are sent to Things by constructing special URL links of the form:
```
things:///commandName?
    parameter1=value1&
    parameter2=value2&
    ...

```
Opening these links will launch the app and execute the command. Here’s how you would tell Things to create a to-do:
```
things:///add?
    title=Buy%20milk&
    notes=High%20fat

```

Support for x-callback-url

All commands support the x-callback-url convention by calling the provided x-success, x-error or x-cancel callbacks as appropriate. Many commands return parameters to the x-success callback.

Getting IDs

Some commands require you to provide IDs of to-dos or lists. Here’s how you can retrieve them in Things.
To get the ID of a to-do:
- On the Mac, control-click on the to-do and choose Share → Copy Link.
- On iOS, tap the to-do to open it and in the toolbar at the bottom, tap  → Share → Copy Link.
To get the ID of a list:
- On the Mac, control-click on the list in the sidebar and choose Share → Copy Link.
- On iOS, navigate into the list and at the top right of the screen, tap  → Share → Copy Link.

Authorization

For security reasons, commands that modify existing Things data require an authorization token to run. This prevents malicious links from modifying your data. This token should be passed as the parameter auth-token along with the other parameters in the command. You can find your unique token in Things’ settings:
- On the Mac, go to Things → Settings → General → Enable Things URLs → Manage.
- On iOS, go to Settings → General → Things URLs.

Data Types

The commands use the following data types for their parameters:
string
	Percent encoded. Maximum un-encoded string length: 4,000 characters unless otherwise specified.
date string
	String. Either today, tomorrow or a date string of the form yyyy-mm-dd. E.g. 2017-09-29. Things will also attempt to interpret natural language dates such as in 3 days or next tuesday. These must be provided in English, regardless of the user’s device language.
time string
	A string describing a time in the local time zone. E.g. 9:30PM or 21:30.
date time string
	A date string followed by the @ symbol and then followed by a time string. E.g. 2018-02-25@14:00.
ISO8601 date time string
	A date-time string conforming to ISO8601. E.g. 2018-03-10T14:30:00Z or 2018-03-10T14:30:00+01:00.
boolean
	A boolean value. Either true or false.
JSON string
	A string in JSON format. See http://www.json.org/ for more details.

Enabling the URL Scheme

The first time you execute a command via the URL scheme, Things will ask you if you want to enable this feature. Simply answer with Enable.
You can later change this in Things’ settings:
- On the Mac, go to Things → Settings → General.
- On iOS, go to Settings → General → Things URLs.

Version

The current version of the URL scheme is 2.

add command

Add a to-do. For example, create a to-do in the inbox:
```
things:///add?
    title=Book%20flights

```
Create a to-do with a tag and notes set to start this evening:
```
things:///add?
    title=Buy%20milk&
    notes=Low%20fat.&
    when=evening&
    tags=Errand

```
Create several to-dos and add them to the Shopping project:
```
things:///add?
    titles=Milk%0aBeer%0aCheese&
    list=Shopping

```
Create and schedule a to-do for next Monday in the Health area (with ID of 3052219D-8039-43D0-8654-AE1E20BE4F56):
```
things:///add?
    title=Call%20doctor&
    when=next%20monday&
    list-id=3052219D-8039-43D0-8654-AE1E20BE4F56

```
Create a to-do in the “This Evening” list with a reminder at 6PM:
```
things:///add?
    title=Collect%20dry%20cleaning&
    when=evening@6pm

```
Note that a limit of 250 items can be added within a 10 second period.

Parameters

All parameters are optional. If neither the when nor list-id are specified, the to-do will be added to the inbox.
title
	String. The title of the to-do to add. Ignored if titles is also specified.
titles
	String separated by new lines (encoded to %0a). Use instead of title to create multiple to-dos. Takes priority over title and show-quick-entry. The other parameters are applied to all the created to-dos.
notes
	String. The text to use for the notes field of the to-do. Maximum unencoded length: 10,000 characters.
when
	String. Possible values: today, tomorrow, evening, anytime, someday, a date string, or a date time string. Using a date time string adds a reminder for that time. The time component is ignored if anytime or someday is specified.
deadline
	Date string. The deadline to apply to the to-do.
tags
	Comma separated strings corresponding to the titles of tags. Does not apply a tag if the specified tag doesn’t exist.
checklist-items
	String separated by new lines (encoded to %0a). Checklist items to add to the to-do (maximum of 100).
use-clipboard
	String. Possible values can be replace-title (newlines overflow into notes, replacing them), replace-notes, or replace-checklist-items (newlines create multiple checklist rows). Takes priority over title, notes, or checklist-items.
list-id
	String. The ID of a project or area to add to. Takes precedence over list.
list
	String. The title of a project or area to add to. Ignored if list-id is present.
heading-id
	String. Takes precedence over heading. The ID of a heading within a project to add to. Ignored if a project is not specified, or if the heading doesn’t exist.
heading
	String. The title of a heading within a project to add to. Ignored if heading-id is present, if a project is not specified, or if the heading doesn’t exist.
completed
	Boolean. Whether or not the to-do should be set to complete. Default: false. Ignored if canceled is also set to true.
canceled
	Boolean. Whether or not the to-do should be set to canceled. Default: false. Takes priority over completed.
show-quick-entry
	Boolean. Whether or not to show the quick entry dialog (populated with the provided data) instead of adding a new to-do. Ignored if titles is specified. Default: false.
reveal
	Boolean. Whether or not to navigate to and show the newly created to-do. If multiple to-dos have been created, the first one will be shown. Ignored if show-quick-entry is also set to true. Default: false.
creation-date
	ISO8601 date time string. The date to set as the creation date for the to-do in the database. Ignored if the date is in the future.
completion-date
	ISO8601 date time string. The date to set as the completion date for the to-do in the database. Ignored if the to-do is not completed or canceled, or if the date is in the future.

Return parameters on x-success

x-things-id
	Comma separated string. The IDs of the to-dos created.

add-project command

Add a project. For example, create a project to build a treehouse set to start today:
```
things:///add-project?
    title=Build%20treehouse&
    when=today

```
Create a project inside the Family area:
```
things:///add-project?
    title=Plan%20Birthday%20Party&
    area=Family

```
Create a project inside the Finance area (with ID of F00A4075-0CA6-4A7F-88C6-CC8B4F1712FC) with a deadline of December 31:
```
things:///add-project?
    title=Submit%20Tax&
    deadline=December%2031&
    area-id=F00A4075-0CA6-4A7F-88C6-CC8B4F1712FC

```

Parameters

All parameters are optional.
title
	String. The title of the project.
notes
	String. The text to use for the notes field of the project. Maximum unencoded length: 10,000 characters.
when
	String. Possible values: today, tomorrow, evening, anytime,  someday, a date string, or a date time string. Using a date time string adds a reminder for that time. The time component is ignored if anytime or someday is specified.
deadline
	Date string. The deadline to apply to the project.
tags
	Comma separated strings corresponding to the titles of tags. Does not apply a tag if the specified tag doesn’t exist.
area-id
	String. The ID of an area to add to. Takes precedence over area.
area
	String. The title of an area to add to. Ignored if area-id is present.
to-dos
	String separated by new lines (encoded to %0a). Titles of to-dos to create inside the project.
completed
	Boolean. Whether or not the project should be set to complete. Default: false. Ignored if canceled is also set to true. Will set all child to-dos to be completed.
canceled
	Boolean. Whether or not the project should be set to canceled. Default: false. Takes priority over completed. Will set all child to-dos to be canceled.
reveal
	Boolean. Whether or not to navigate into the newly created project. Default: false.
creation-date
	ISO8601 date time string. The date to set as the creation date for the project in the database. If the to-dos parameter is also specified, this date is applied to them, too. Ignored if the date is in the future.
completion-date
	ISO8601 date time string. The date to set as the completion date for the project in the database. If the to-dos parameter is also specified, this date is applied to them, too. Ignored if the to-do is not completed or canceled, or if the date is in the future.

Return parameters on x-success

x-things-id
	string. The ID of the project created.

update command

Update an existing to-do. For example, set a to-do to start today:
```
things:///update?
    id=4BE64FEA-8FEF-4F4F-B8B2-4E74605D5FA5&
    when=today

```
Change the title of a to-do:
```
things:///update?
    id=4BE64FEA-8FEF-4F4F-B8B2-4E74605D5FA5&
    title=Buy%20bread

```
Append notes to a to-do:
```
things:///update?
    id=4BE64FEA-8FEF-4F4F-B8B2-4E74605D5FA5&
    append-notes=Wholemeal%20bread

```
Add some checklist items to a to-do:
```
things:///update?
    id=4BE64FEA-8FEF-4F4F-B8B2-4E74605D5FA5&
    append-checklist-items=Cheese%0aBread%0aEggplant

```
Remove the deadline from a to-do:
```
things:///update?
    id=4BE64FEA-8FEF-4F4F-B8B2-4E74605D5FA5&
    deadline=

```

Parameters

id and auth-token must be specified. All other parameters are optional. Including a parameter with an equals sign (=) but without a value will clear that value (see deadline example).
auth-token
	String. The Things URL scheme authorization token.
id
	String. The ID of the to-do to update. Required.
title
	String. The title of the to-do. This will replace the existing title.
notes
	String. The notes of the to-do. This will replace the existing notes. Maximum unencoded length: 10,000 characters.
prepend-notes
	String. Text to add before the existing notes of a to-do. Maximum unencoded length: 10,000 characters.
append-notes
	String. Text to add after the existing notes of a to-do. Maximum unencoded length: 10,000 characters.
when
	String. Set the when field of a to-do. Possible values: today, tomorrow, evening, someday, a date string, or a date time string. Including a time adds a reminder for that time. The time component is ignored if someday is specified. This field cannot be updated on repeating to-dos.
deadline
	Date string. The deadline to apply to the to-do. This field cannot be updated on repeating to-dos.
tags
	Comma separated strings corresponding to the titles of tags. Replaces all current tags. Does not apply a tag if the specified tag doesn’t exist.
add-tags
	Comma separated strings corresponding to the titles of tags. Adds the specified tags to a to-do. Does not apply a tag if the specified tag doesn’t exist.
checklist-items
	n (encoded to %0a) separated strings. Set the checklist items of the to-do (maximum of 100). Will replace all existing checklist items.
prepend-checklist-items
	n (encoded to %0a) separated strings. Add checklist items to the front of the list of checklist items in the to-do (maximum of 100).
append-checklist-items
	n (encoded to %0a) separated strings. Add checklist items to the end of the list of checklist items in the to-do (maximum of 100).
list-id
	String. The ID of a project or area to move the to-do into. Takes precedence over list.
list
	String. The title of a project or area to move the to-do into. Ignored if list-id is present.
heading-id
	String. Takes precedence over heading. The ID of a heading within a project to move the to-do to. Ignored if the to-do is not in a project with the specified heading. Can be used together with list or list-id.
heading
	String. The title of a heading within a project to move the to-do to. Ignored if heading-id is present, or if the to-do is not in a project with the specified heading. Can be used together with list or list-id.
completed
	Boolean. Complete a to-do or set a to-do to incomplete. Ignored if canceled is also set to true. Setting completed=false on a canceled to-do will also mark it as incomplete. This field cannot be updated on repeating to-dos.
canceled
	Boolean. Cancel a to-do or set a to-do to incomplete. Takes priority over completed. Setting canceled=false on a completed to-do will also mark it as incomplete. This field cannot be updated on repeating to-dos.
reveal
	Boolean. Whether or not to navigate to and show the updated to-do. Default: false.
duplicate
	Boolean. Set to true to duplicate the to-do before updating it, leaving the original to-do untouched. Repeating to-dos cannot be duplicated. Default: false.
creation-date
	ISO8601 date time string. Set the creation date for the to-do in the database. Ignored if the date is in the future.
completion-date
	ISO8601 date time string. Set the completion date for the to-do in the database. Ignored if the to-do is not completed or canceled, or if the date is in the future. This field cannot be updated on repeating to-dos.

Return parameters on x-success

x-things-id
	String. The ID of the to-do updated.

update-project command

Update an existing project. For example, set a project to start tomorrow:
```
things:///update-project?
    id=852763FD-5954-4DF9-A88A-2ADD808BD279&
    when=tomorrow

```
Add a tag to a project:
```
things:///update-project?
    id=852763FD-5954-4DF9-A88A-2ADD808BD279&
    add-tags=Important

```
Prepend notes to a project:
```
things:///update-project?
    id=852763FD-5954-4DF9-A88A-2ADD808BD279&
    prepend-notes=SFO%20to%20JFK.

```
Clear the deadline of a project:
```
things:///update-project?
    id=852763FD-5954-4DF9-A88A-2ADD808BD279&
    deadline=

```

Parameters

id and auth-token must be specified. All other parameters are optional. Including a parameter with an equals sign (=) but without a value will clear that value (see deadline example).
auth-token
	String. The Things URL scheme authorization token.
id
	String. The ID of the project to update. Required.
title
	String. The title of the project. This will replace the existing title.
notes
	String. The notes of the project. This will replace the existing notes. Maximum unencoded length: 10,000 characters.
prepend-notes
	String. Text to add before the existing notes of a project. Maximum unencoded length: 10,000 characters.
append-notes
	String. Text to add after the existing notes of a project. Maximum unencoded length: 10,000 characters.
when
	String. Set the when field of a project. Possible values: today, tomorrow, evening, someday, a date string, or a date time string. Including a time adds a reminder for that time. The time component is ignored if someday is specified. This field cannot be updated on repeating projects.
deadline
	Date string. The deadline to apply to the project. This field cannot be updated on repeating projects.
tags
	Comma separated strings corresponding to the titles of tags. Replaces all current tags. Does not apply a tag if the specified tag doesn’t exist.
add-tags
	Comma separated strings corresponding to the titles of tags. Adds the specified tags to a project. Does not apply a tag if the specified tag doesn’t exist.
area-id
	String. The ID of an area to move the project into. Takes precedence over area.
area
	String. The title of an area to move the project into. Ignored if area-id is present.
completed
	Boolean. Complete a project or set a project to incomplete. Ignored if canceled is also set to true. Setting to true will be ignored unless all child to-dos are completed or canceled and all child headings archived. Setting  to false on a canceled project will mark it as incomplete. This field cannot be updated on repeating projects.
canceled
	Boolean. Cancel a project or set a project to incomplete. Takes priority over completed. Setting to true will be ignored unless all child to-dos are completed or canceled and all child headings archived. Setting to false on a completed project will mark it as incomplete. This field cannot be updated on repeating projects.
reveal
	Boolean. Whether or not to navigate to and show the updated project. Default: false.
duplicate
	Boolean. Set to true to duplicate the project before updating it, leaving the original project untouched. Repeating projects cannot be duplicated. Default: false.
creation-date
	ISO8601 date time string. Set the creation date for the project in the database. Ignored if the date is in the future.
completion-date
	ISO8601 date time string. Set the completion date for the project in the database. Ignored if the project is not completed or canceled, or if the date is in the future. This field cannot be updated on repeating projects.

Return parameters on x-success

x-things-id
	String. The ID of the project updated.

show command

Navigate to and show an area, project, tag or to-do, or one of the built-in lists, optionally filtering by one or more tags.
Navigate to the Today list:
```
things:///show?
    id=today

```
Show to-do with ID 8796CC16E-92FA-4809-9A26-36194985E87B:
```
things:///show?
    id=8796CC16E-92FA-4809-9A26-36194985E87B

```
Navigate into project with ID 9096CC16E-92FA-4809-9A26-36194985E44A:
```
things:///show?
    id=9096CC16E-92FA-4809-9A26-36194985E44A

```
Show project with title “Vacation”:
```
things:///show?
    query=vacation

```
Show project with title “Vacation”, filtering by the “Errand” tag:
```
things:///show?
    query=vacation&
    filter=errand

```

Parameters

Either id or query must be specified; filter is optional.
id
	String. The ID of an area, project, tag or to-do to show; or one of the following built-in list IDs: inbox, today, anytime, upcoming, someday, logbook, tomorrow, deadlines, repeating, all-projects, logged-projects. Takes precedence over query.
query
	String. The name of an area, project, tag or a built-in list to show. This is equivalent to entering the query text in to the quick find within Things and selecting the first result. Ignored if id is also set. Note: task cannot be shown using the query parameter; use the id parameter or the search command instead.
filter
	String. Comma separated strings corresponding to the titles of tags that the list should be filtered by.

Return parameters on x-success

none

search command

Invoke and show the search screen. For example, search for the text “vacation”:
```
things:///search?
    query=vacation

```
Show the search screen without searching for anything:
```
things:///search

```

Parameters

All parameters are optional.
query
	String. The search query.

Return parameters on x-success

none

version command

The version of the Things app and URL scheme.
```
things:///version

```

Parameters

none

Return parameters on x-success

x-things-scheme-version
	String. The version of the Things URL scheme.
x-things-client-version
	String. The build number of the app.

json command (for Developers)

Things also has an advanced, JSON-based add command that allows more control over the projects and to-dos imported into Things. This command is intended to be used by app developers or other people familiar with scripting or programming.
We’ve created a set of Swift helper classes that you can use to more easily generate the JSON needed for this command. Get the code from the Things JSON Coder GitHub repository.
Example:
```
things:///json?data=
  [
    {
      "type": "project",
      "attributes": {
        "title": "Go Shopping",
        "items": [
          {
            "type": "to-do",
            "attributes": {
              "title": "Bread"
            }
          },
          {
            "type": "to-do",
            "attributes": {
              "title": "Milk"
            }
          }
        ]
      }
    }
  ]

```

Parameters

auth-token
	String. The Things URL scheme authorization token. This is required whenever the provided JSON data contains an update operation.
data
	JSON string. The JSON should be an array containing to-do and project objects (see below).
reveal
	Boolean. Whether or not to navigate to and show the newly created to-do or project. If multiple items have been created, the first one will be shown. Default: false.

Return parameters on x-success

x-things-ids
	JSON string. An array of IDs of the to-dos and projects created that were specified in the top level JSON array. The IDs of the to-dos created inside projects are not returned.

Describing Things objects in JSON

Each operation consists of the following fields:
- type The type of the object. These are described in more detail below. This field is required.
- operation The operation to perform on the object. Either create (create a new object) or update (update the fields of an existing object). If this field is not present, the operation is assumed to be create. Currently only to-do and project objects can be updated.
- id Required for update operations, this is the ID of the object to update.
- attributes A dictionary of attributes, which correspond to the properties of the object itself. The attributes field must be included but all attributes themselves are optional.
```
{
    "type": "to-do",
    "operation": "update",
    "id": "1BD13549-0BE7-49AC-B645-74B7BA8DE7C4",
    "attributes": {
        "deadline": "today"
    }
}

```

To-do

```
{
  "type": "to-do",
  "attributes": {
    "title": "Milk"
  }
}

```
- type is to-do.
- attributes: 		
	- title - string. The title of the to-do.
	- notes - string. The text to use for the notes field of the to-do. Maximum length: 10,000 characters.
	- when - string. Possible values: today, tomorrow, evening, anytime, someday, a date string, or a date time string. Using a date time string adds a reminder for that time. The time component is ignored if anytime or someday is specified.
	- deadline - date string. The deadline to apply to the to-do.
	- tags - array of strings corresponding to the titles of tags. Does not apply a tag if a tag with the specified title doesn’t exist.
	- checklist-items - array of checklist-item objects (maximum of 100).
	- list-id - string. The ID of a project or area to add to. Takes precedence over list. Ignored if the to-do is specified inside the items array of a project object.
	- list - string. The title of a project or area to add to. Ignored if list-id is present, or if the to-do is specified inside the items array of a project object.
	- heading-id - string. Takes precedence over heading. The ID of a heading within a project to add to. Ignored if a project is not specified, if the heading doesn’t exist, or if the to-do is specified inside the items array of a project object.
	- heading - string. The title of a heading within a project to add to. Ignored if heading-id is present, if a project is not specified, if the heading doesn’t exist, or if the to-do is specified inside the items array of a project object.
	- completed - boolean. Whether or not the to-do should be set to complete. Default: false. Ignored if canceled is also set to true.
	- canceled - boolean. Whether or not the to-do should be set to canceled. Default: false. Takes priority over completed.
	- creation-date - ISO8601 date time string. The date to set as the creation date for the to-do in the database. Ignored if the date is in the future.
	- completion-date - ISO8601 date time string. The date to set as the completion date for the to-do in the database. Ignored if the to-do is not completed or canceled, or if the date is in the future.
- update specific attributes. These attributes can only be used with update operations: 		
	- prepend-notes - string. Text to add before the existing notes of a to-do. Maximum unencoded length: 10,000 characters.
	- append-notes - string. Text to add after the existing notes of a to-do. Maximum unencoded length: 10,000 characters.
	- add-tags - comma separated strings corresponding to the titles of tags. Adds the specified tags to a to-do. Does not apply a tag if the specified tag doesn’t exist.
	- prepend-checklist-items - n (encoded to %0a) separated strings. Add checklist items to the front of the list of checklist items in the to-do (maximum of 100).
	- append-checklist-items - n (encoded to %0a) separated strings. Add checklist items to the end of the list of checklist items in the to-do (maximum of 100).

Project

```
{
  "type": "project",
  "attributes": {
    "title": "Go Shopping",
    "items": [
      {
        "type": "to-do",
        "attributes": {
          "title": "Bread"
        }
      }
    ]
  }
}

```
- type is project.
- attributes: 		
	- title - string. The title of the project.
	- notes - string. The text to use for the notes field (maximum length: 10,000 characters).
	- when - string. Possible values: today, tomorrow, evening, anytime, someday, a date string, or a date time string. Using a date time string adds a reminder for that time. The time component is ignored if anytime or someday is specified.
	- deadline - date string. The deadline to apply.
	- tags - array of strings corresponding to the titles of tags. Does not apply a tag if a tag with the specified title doesn’t exist.
	- area-id - string. The ID of an area to add to. Takes precedence over area.
	- area - string. The title of an area to add to. Ignored if area-id is present.
	- completed - boolean. Whether or not the project should be set to complete. Default: false. Ignored unless all child to-dos are completed or canceled.
	- canceled - boolean. Whether or not the project should be set to canceled. Default: false. Takes priority over completed. Ignored unless all child to-dos are completed or canceled.
	- creation-date - ISO8601 date time string. The date to set as the creation date for the project in the database. Ignored if the date is in the future.
	- completion-date - ISO8601 date time string. The date to set as the completion date for the project in the database. Ignored if the project is not completed or canceled, or if the date is in the future.
- create specific attributes. These attributes can only be used with create operations: 		
	- items - array of to-do or heading objects. To add to-dos to an existing project, create individual to-do objects instead.
- update specific attributes. These attributes can only be used with update operations: 		
	- prepend-notes String. Text to add before the existing notes of a project. Maximum unencoded length: 10,000 characters.
	- append-notes String. Text to add after the existing notes of a project. Maximum unencoded length: 10,000 characters.
	- add-tags Comma separated strings corresponding to the titles of tags. Adds the specified tags to a project. Does not apply a tag if the specified tag doesn’t exist.

Heading

```
{
  "type": "heading",
  "attributes": {
    "title": "Sights"
  }
}

```
- type is heading.
- attributes: 		
	- title - string. The title of the heading.
	- archived - boolean. Whether or not the heading is archived. Default: false. Ignored unless all to-dos under the heading are completed or canceled.

Checklist Item

```
{
  "type": "checklist-item",
  "attributes": {
    "title": "Hotels",
    "completed": true
  }
}

```
- type is checklist-item.
- attributes: 		
	- title - string. The title of the checklist item.
	- completed - boolean. Whether or not the checklist item should be set to complete. Default: false. Ignored if canceled is also set to true.
	- canceled - boolean. Whether or not the checklist item should be set to canceled. Default: false. Takes priority over completed.

JSON Example

This example is not URL encoded for clarity.
```
things:///json?data=
  [
    {
      "type": "project",
      "attributes": {
        "title": "Go Shopping",
        "items": [
          {
            "type": "to-do",
            "attributes": {
              "title": "Bread"
            }
          },
          {
            "type": "to-do",
            "attributes": {
              "title": "Milk"
            }
          }
        ]
      }
    },
    {
      "type": "project",
      "attributes": {
        "title": "Vacation in Rome",
        "notes": "Some time in August.",
        "area": "Family",
        "items": [
          {
            "type": "to-do",
            "attributes": {
              "title": "Ask Sarah for travel guide"
            }
          },
          {
            "type": "to-do",
            "attributes": {
              "title": "Add dates to calendar"
            }
          },
          {
            "type": "heading",
            "attributes": {
              "title": "Sights"
            }
          },
          {
            "type": "to-do",
            "attributes": {
              "title": "Vatican City"
            }
          },
          {
            "type": "to-do",
            "attributes": {
              "title": "The Colosseum",
              "notes": "12€"
            }
          },
          {
            "type": "heading",
            "attributes": {
              "title": "Planning"
            }
          },
          {
            "type": "to-do",
            "attributes": {
              "title": "Call Paolo",
              "completed": true
            }
          },
          {
            "type": "to-do",
            "attributes": {
              "title": "Book flights",
              "when": "today"
            }
          },
          {
            "type": "to-do",
            "attributes": {
              "title": "Research",
              "checklist-items": [
                {
                  "type": "checklist-item",
                  "attributes": {
                    "title": "Hotels",
                    "completed": true
                  }
                },
                {
                  "type": "checklist-item",
                  "attributes": {
                    "title": "Transport from airport"
                  }
                }
              ]
            }
          }
        ]
      }
    },
    {
      "type": "to-do",
      "attributes": {
        "title": "Pick up dry cleaning",
        "when": "evening",
        "tags": [
          "Errand"
        ]
      }
    },
    {
      "type": "to-do",
      "attributes": {
        "title": "Submit report",
        "deadline": "2018-02-01",
        "list": "Work"
      }
    }
  ]

```

URL Encoded Example

All of the above JSON examples must have the white space removed and then be URL encoded before they can be used. For example:
```
things:///json?data=
  [
    {
      "type": "to-do",
      "attributes": {
        "title": "Buy milk"
      }
    }
  ]

```
After removing white space:
```
things:///json?data=[{"type":"to-do","attributes":{"title":"Buy milk"}}]

```
After URL encoding:
```
things:///json?data=%5B%7B%22type%22:%22to-do%22,%22attributes%22:%7B%22title%22:%22Buy%20milk%22%7D%7D%5D

```

add-json command

Deprecated. The json command can be used for adding items via JSON.

Related Articles

- Things Shortcuts Actions
- Using AppleScript

