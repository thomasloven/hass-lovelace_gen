# lovelace_gen

`configuration.yaml`
```yaml
lovelace_gen:
```

Regenerate by using the "Refresh" function in lovelace.

![refresh](https://user-images.githubusercontent.com/1299821/62565489-2e655780-b887-11e9-86a1-2de868a4dc7d.png)

## Example
`ui_lovelace.yaml`
```yaml
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
  - !include floorplan.yaml {"lamps":"true", "title":"With Lamps"}

# Use this if you want lovelace_gen to ignore the jinja
{% raw %}
  - type: markdown
    content: |
      # Coming soon(?)

      A built-inmarkdown card with jinja templating.
      So I can tell that my light is {{ states('light.bed_light') }}!
{% endraw %}

  - !include floorplan.yaml {"title":"No lights"}
```

`lovelace/floorplan.yaml`
```yaml
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

