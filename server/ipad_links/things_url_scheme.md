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
