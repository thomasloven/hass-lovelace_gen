lovelace\_gen
============

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

Improve the Home Assistant Dashboard YAML parser by adding Python functionality for more robust **generation** of Jinja2 templates. This integration changes the way Home Assistant parses your `ui-lovelace.yaml` and/or other configured Dashboard .yaml files before sending the information off to the Dashboard frontend in your browser. It's only useful on those Dashboards configured to use [YAML mode](https://www.home-assistant.io/lovelace/yaml-mode/).

See [my floorplan card](https://github.com/thomasloven/hass-config/blob/master/lovelace/floorplan.yaml) for an example of what's possible.

# Installation

- Copy the contents of `custom_components/lovelace_gen/` to `/config/custom_components/lovelace_gen/`.
- Add the following:
  - to `configuration.yaml` if you intend to implement lovelace_gen functionality with your main default (i.e. Overview) Dashboard.
    ```yaml
    lovelace_gen:

    lovelace:
      mode: yaml
    ```
  - and/or [all of your dashboards](https://www.home-assistant.io/dashboards/dashboards/) that you have set to yaml mode and would like to implement lovelace_gen functionality:
    ```yaml
    dashboards:
      yaml-home:
        mode: yaml
        filename: DashboardHome.yaml
        title: Home
        icon: mdi:home-account
        show_in_sidebar: true
        require_admin: false
      yaml-sandbox:
        mode: yaml
        filename: YAMLSandbox.yaml
        title: YAML Sandbox
        icon: mdi:timer-sand-paused
        show_in_sidebar: true
        require_admin: true
    ```
- Restart Home Assistant

# Configuration

Keep the following in mind as you configure your Dashboards to implement lovelace_gen functionality:

- Any .yaml Dashboard file that is to be processed with `lovelace_gen` *MUST* have the following as the first line of an included .yaml file:
  - ui-lovelace.yaml or DashboardHome.yaml, etc.
    ```yaml
    title: Home
    views: !include ui-lovelace-included.yaml
    ```
  - ui-lovelace-included.yaml or DashboardHome_Included.yaml, etc.
    ```yaml
    # lovelace_gen
    ```
    **I do not know why this is necessary, but it's how you must configure your Dashboard for lovelace_gen to work.**

- To rerender the frontend, use the Refresh option from the three-dots-menu in Lovelace

![refresh](https://user-images.githubusercontent.com/1299821/62565489-2e655780-b887-11e9-86a1-2de868a4dc7d.png)

# Added Functionality!

The changes from the default Dashboard generation include

## Jinja2 templates

You can now use [Jinja2 templates](https://jinja.palletsprojects.com/en/3.0.x/templates/) in your Dashboard configuration similar to how templates can already be used in other sections of Home Assistant.

Some examples of how this can be used include the following:

- Set and use variables
```yaml
{% set my_lamp = "light.bed_light" %}

type: entities
entities:
 - {{ my_lamp }}
```

- Loop through lists
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
Please note that for this to work, the indentation of the code in the macro block *must* exactly where it will be called.

- Add conditional parts
```yaml
{% if myvariable == true %}
Do something
{% endif %}
```

This is NOT dynamic. The values of variables are locked down when you rerender the interface.

This might make conditions seem pointless... but they work well with the next feature.

## Passing arguments to included files

Normally, you can include a file in your Lovelace configuration using

```yaml
view:
  - !include lovelace/my_view.yaml
```

`lovelace_gen` lets you add a second argument to that function. This second argument is a dictionary of variables and their values, that will be set for all Jinja2 templates in the new file:

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
> The `fromjson` filter is a feature of `lovelace_gen` and not normally included in Jinja2.

## Invalidate cache of files

If you use lots of custom Lovelace cards, chances are that you have run into caching problems at one point or another.

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

## Example Dashboard Configurations
`ui-lovelace.yaml`
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

# Use this if you want lovelace_gen to ignore the Jinja2
{% raw %}
  - type: markdown
    content: |
      # Coming soon(?)

      A built-inmarkdown card with Jinja2 templating.
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

### How can I use global variables?
You can add variables to the `lovelace_gen` configuration in `configuration.yaml` and then reference them in lovelace using `{{ _global }}`.

For example:
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

### What if I WANT Jinja2 in my Lovelace interface
Use the `{% raw %}` and `{% endraw %}` tags. See [this example](#example-dashboard-configurations).

### Is there any way to solve the indentation problem for macros
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
