lovelace\_gen
============

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Improve the lovelace yaml parser for Home Assistant.

See [my floorplan card](https://github.com/thomasloven/hass-config/blob/master/lovelace/floorplan.yaml) for an example of what's possible.

This fork includes a configuration option to change the `{}` delimiters used by Jinja to disambiguate them from those of Home Assistant templates.

# Installation instructions

- Copy the contents of `custom_components/lovelace_gen/` to `<your config dir>/custom_components/lovelace_gen/`.
- Add the following to your `configuration.yaml`:

```yaml
lovelace_gen:

lovelace:
  mode: yaml
```

- Restart Home Assistant

# Usage

This integration changes the way Home Assistant parses your `ui_lovelace.yaml` before sending the information off to the lovelace frontend in your browser. It's obviously only useful if you are using [YAML mode](https://www.home-assistant.io/lovelace/yaml-mode/).

### First of all
To rerender the frontend, use the Refresh option from the three-dots-menu in Lovelace

![refresh](https://user-images.githubusercontent.com/1299821/62565489-2e655780-b887-11e9-86a1-2de868a4dc7d.png)

### Second of all

Any yaml file that is to be processed with `lovelace_gen` *MUST* have the following as its first line:

```yaml
# lovelace_gen
```
**Important:** For some reason, which I can't seem to nail down, things stop working if you add `# lovelace_gen` to `ui-lovelace.yaml`. Adding it to *any* file *included from* `ui-lovelace.yaml` works, though.

### Third of all

Assuming you already have included the first line above, you may optionally include the following as the second line:

```yaml
# lovelace_gen_config []
```
This will then replace the usual Jinja delimiters of `{` and `}` with `[` and `]`. This means instead of coding `{{ ... }}`, you would code `[[ ...]]`, and instead of
`{% ... %}` you would use `[% ... %]`. This makes it easier to intersperse `lovelace_gen` code with Home Assistant Template code. For example:

```yaml
{% raw% }{{ states('{% endraw %}{{ entity }}{% raw %}') }}{% endraw %}
```

Becomes:

```yaml
{{ states('[[ entity ]]') }}
```

This takes effect from "here down". If you want a later file to revert to the default behavior, include the following as the second line:

```yaml
# lovelace_gen_config {}
```

### Let's continue

The changes from the default generation include

## Jinja2 templates

You can now use [Jinja2](https://jinja.palletsprojects.com/en/2.10.x/templates/) templates in your lovelace configuration.

This can be used e.g. to

- Set and use variables
```yaml
{% set my_lamp = "light.bed_light" %}

type: entities
entities:
 - {{ my_lamp }}
```

- Loop over lists
```yaml
{% set lights = ['light.bed_light', 'light.kitchen_lights', 'light.ceiling_lights'] %}

- type: entities
  entities:
  {% for l in lights %}
    - {{ l }}
  {% endfor %}

- type: horizontal-stack
  cards:
    {% for l in lights %}
    - type: light
      entity: {{ l }}
    {% endfor %}
```

- Use macros
```yaml
{% macro button(entity) -%}
  - type: entity-button
    entity: {{ entity }}
    tap_action:
      action: more-info
    hold_action:
      action: toggle
{%- endmacro %}

type: horizontal-stack
cards:
  {{ button("light.bed_light") }}
  {{ button("light.ceiling_lights") }}
  {{ button("light.kitchen_lights") }}

```
Please note that for this to work, the indentation of the code in the macro block *must* be equal to what it should be where it's called.

- Add conditional parts
```yaml
{% if myvariable == true %}
Do something
{% endif %}
```

This is NOT dynamic. The values of variables are locked down when you rerender the interface.

This might make conditions seem pointless... but they work well with the next feature.

## Passing arguments to included files

Normally, you can include a file in your lovelace configuration using

```yaml
view:
  - !include lovelace/my_view.yaml
```

`lovelace_gen` lets you add a second argument to that function. This second argument is a dictionary of variables and their values, that will be set for all jinja2 templates in the new file:

```yaml
type: horizontal-stack
cards:
  - !include
    - button_card.yaml
    - entity: light.bed_light
  - !include
    - button_card.yaml
    - entity: switch.decorative_lights
  - !include
    - button_card.yaml
    - entity: light.ceiling_lights
      name: LIGHT!
```

`button_card.yaml`
```yaml
# lovelace_gen
{% if entity.startswith("light") %}
type: light
{% else %}
type: entity-button
{% endif %}
entity: {{ entity }}
name: {{ name }}
```

![include args](https://user-images.githubusercontent.com/1299821/62578438-6d080b80-b8a1-11e9-892f-f223fa5452c0.png)


Be careful about the syntax here. Note that the arguments are given as a list and is indented under the `!include` statement. The second item in the list is a dictionary.

> Note: If you want to pass a dictionary of values into a file, you need to convert it to json first:
> ```yaml
> {% set mydict = {"a": 1, "b": 2} %}
> variable: {{ mydict | tojson }}
> ```
> And then convert it back from json inside the file:
> ```yaml
> content: The value of a is {{ (variable | fromjson)['a'] }}
> ```
>
> The `fromjson` filter is a feature of `lovelace_gen` and not normally included in jinja.

## Invalidate cache of files

If you use lots of custom lovelace cards, chances are that you have run into caching problems at one point or another.

I.e. you refresh your page after updating the custom card, but nothing changes.

The answer is often to add a counter after the URL of your resource, e.g.

```yaml
resources:
  - url: /local/card-mod.js?v=2
    type: module
```

`lovelace_gen` introduces a `!file` command that handles this for you.

```yaml
resources:
  - url: !file /local/card-mod.js
    type: module
```

After this, `lovelace_gen` will automatically add a random version number to your URL every time you rerender the frontend. You won't have to worry about cache ever again.

This can also be used for pictures.

## Example
`ui_lovelace.yaml`
```yaml
# lovelace_gen
resources:
  # When you regenerate, the browser cache for this file will be invalidated
  - url: !file /local/card-mod.js
    type: module
...

views:
 - ! include lovelace/my_cool_view.yaml
```

`lovelace/my_cool_view.yaml`
```yaml
# lovelace_gen
{% set my_lights = ["light.bed_light", "light.kitchen_lights", "light.ceiling_lights"] %}
title: My view
cards:
  - type: entities
    entities:
{% for light in my_lights %}
      - {{ light }}
{% endfor %}

  # Include files with arguments
  # NB: JSON format for arguments
  # And NO SPACE after the colons!
  - !include
    -floorplan.yaml
    - lamps: true
      title: With Lamps

# Use this if you want lovelace_gen to ignore the jinja
{% raw %}
  - type: markdown
    content: |
      # Coming soon(?)

      A built-inmarkdown card with jinja templating.
      So I can tell that my light is {{ states('light.bed_light') }}!
{% endraw %}

  - !include
    - floorplan.yaml
    - title: No lights
```

`lovelace/floorplan.yaml`
```yaml
# lovelace_gen
{% macro lamp(entity, x, y) -%}
{% if lamps %}
- type: state-icon
  entity: {{ entity }}
{% else %}
- type: custom:gap-card
{% endif %}
  style:
    left: {{ x }}%
    top: {{ y }}%
{%- endmacro %}

type: picture-elements
title: {{ title }}
image: https://placekitten.com/800/600
elements:
  {{ lamp('light.bed_light', 25, 25) }}
  {{ lamp('light.kitchen_lights', 50, 25) }}
  {{ lamp('light.ceiling_lights', 50, 50) }}
```

![lovelace_gen](https://user-images.githubusercontent.com/1299821/62565373-ecd4ac80-b886-11e9-9dcb-c41b43027b2b.png)

## Hidden bonus
With lovelace_gen installed, you'll be able to redefine node anchors in the same file. A feature in the YAML specification, but an error in the engine Home Assistant normally uses...

# FAQ

### How can I do global variables?
You can add variables to the `lovelace_gen` configuration in `configuration.yaml` and then refernce them in lovelace using `{{ _global }}`.

E.g.:
```yaml
lovelace_gen:
  rooms:
    - living_room
    - kitchen
    - bed_room
```

```yaml
type: entities
entities:
  {% for room in _global.rooms %}
  - type: custom:auto-entities
    card:
      type: custom:fold-entity-row
      head:
        type: section
        label: {{ room|capitalize }}
    filter:
      include:
        - area: {{ room }}
  {% endfor %}
```

### Can I use this for my general Home Assistant configuration?
It's called **lovelace**\_gen for a reason...
That being said - it *might* work. Or it might not. There's really no way to
tell. It depends on what parts of the configuration are loaded before or after
lovelace_gen itself.

I'd advice you not to try it.


### What if I WANT jinja in my lovelace interface
Use the `{% raw %}` and `{% endraw %}` tags. There's an example above. Alternatively, you can change `lovelace_gen` to use different characters, as mentioned above under
[Third of all](hass-lovelace_gen#first-of-all).


### How do I avoid "bad indentation of a mapping entry" or "missed comma between flow collection entries" in VS Code?
If a line only contains `lovelace-gen` code, you can start that line as a comment, and the code will still run. The resultant output from the generation will contain these
comments, but if they end up on a line of their own, they should do no harm.

### Is there any way to solve the indentation problem for macros?
Not automatically, but you can do something like
```yaml
{% macro button(entity, ws) %}
{{"  "*ws}}- type: entity-button
{{"  "*ws}}  entity: {{ entity }}
{{"  "*ws}}  tap_action:
{{"  "*ws}}    action: more-info
{{"  "*ws}}  hold_action:
{{"  "*ws}}    action: toggle
{%- endmacro %}

  - type: horizontal-stack
    cards:
      {{ button('light.bed_light', 3) }}

  {{ button('light.bed_light', 1) }}
```

Note that included files don't have this problem.

---
<a href="https://www.buymeacoffee.com/uqD6KHCdJ" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/white_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
