---
id: variables
title: Variables
---

Variables are placeholders that can be used to dynamically insert values in your app. They are available in processors and output of your app. You can use a variable by clicking on the variable from the dropdown below any text area, expand the step and click on the variable to insert in the text field.

:::note
Both the input fields as well the output from all the processors in the app are available as variables. Only the variables from previous steps are available in a given step. For example, if you are in step 3, you can only use variables from steps 1 and 2. You can use variables from the input and outputs of all processors in output.
:::

## Variable format

Variables are defined in the following format:

```
{{step_name.field_name}}
```

where `step_name` is of the format `_inputs<step_number>` and `field_name` is the name of the field in the step. For example, for input fields, the variable format is:

:::note
`step_number` starts from 0. So to access app input fields, use `_inputs0` as the step name.
:::

```
{{_inputs1.field_name}}
```

where `field_name` is the name of the input field. In most cases, you do not see this format but instead see a pill of form `[step_number] processor_name / field_name`.

## Advanced usage

For more advanced uses, LLMStack supports the use of [liquidjs templates](https://liquidjs.com/tutorials/intro-to-liquid.html) as variables in `Output`. Liquid is a templating language that allows you to use variables, conditionals, and loops to manipulate data. Data to liquidjs template is available as an object with `_inputs<step_number>` as key and the input fields or processor output as value. For example, if you want to access the `text` field from the input of step 1, you can use the following liquidjs template:

```
{{_inputs1.text}}
```

:::note
In most cases, you will only see pills of form `[step_number] processor_name / field_name` when you select the variable from the variables dropdown
:::
