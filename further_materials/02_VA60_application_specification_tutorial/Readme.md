- [Getting Started with Open Recon application specifications](#getting-started-with-open-recon-application-specifications)
  - [A First Overview](#a-first-overview)
    - [Step 1: Get started](#step-1-get-started)
    - [Step 2: Fill in descriptive information](#step-2-fill-in-descriptive-information)
    - [Step 3: Define the environment for your application](#step-3-define-the-environment-for-your-application)
    - [Step 4: Define the UI for your application](#step-4-define-the-ui-for-your-application)
  - [The `reconstruction` Section](#the-reconstruction-section)
    - [Step 1: Choose your emitter and injector points](#step-1-choose-your-emitter-and-injector-points)
    - [Step 2: Describe your hardware](#step-2-describe-your-hardware)
    - [Step 3: Describe expectations on the environment](#step-3-describe-expectations-on-the-environment)
  - [The `parameter` section](#the-parameter-section)
    - [Step 1: Create a numerical parameter](#step-1-create-a-numerical-parameter)
    - [Step 2: Create a string parameter](#step-2-create-a-string-parameter)
    - [Step 3: Create an enum parameter](#step-3-create-an-enum-parameter)
- [Conclusion](#conclusion)

# Getting Started with Open Recon application specifications

Open Recon uses Docker images to package applications. However, additional information needs to be provided about the expectations of the environment. An example here is whether a reconstruction of raw data or an operations on images should be performed. All of this is provided by the **Application Specification**.
It even includes the information about how Open Recon sets up the graphical user interface to pass parameters to the reconstruction. 

This section of the tutorial teaches you what the application specification of an Open Recon application is, what options it provides, and which constraints and structure you have to follow for your own application.

---

## A First Overview

### Step 1: Get started

Open the [application_specification_template.json](application_specification_template.json). It contains a minimal example for an application specification file.
To show you how the tools in this devcontainer help you debug your JSON files,

        ToDo: delete a single line from the "general" section.

Now, hover over the "general" keyword. A hint appears indicating a "Missing property ...".
This results from the configuration of the devcontainer checking the JSON against the provided schema in [application_specification_schema.json](application_specification_schema.json).

If you prefer command-line tools, then you can check the validity of your application specification JSON file with:

```bash
python -m check_jsonschema application_specification_template.json \
  --schemafile application_specification_schema.json
```

### Step 2: Fill in descriptive information

The template contains four "TODO" items all located under "general":

1. `id`: describes the actual name of the application which is independent of the language settings of the environment. Fill it with a name for your application.
2. `vendor`: is language-independent and should refer to you as a person or your institution.
3. `name`: is an end-user-visible string and can be identical to `id`. It supports English language settings which is indicated by the `en` key.
4. `information`: is an end-user-visible string used to convey information about your application. It supports English language settings which is indicated by the `en` key.


### Step 3: Define the environment for your application

Next, we concentrate on the `reconstruction` section.
This section of the application specification contains all the details about the executed task within the docker container.
An important element is the pair of `emitter` and `injector`. You can see that this example configures an image to image method (i2i).
The following sections include request for RAM and CPU cores with `min_required_memory` and `min_count_required_cpu_cores`. Take note that minimum refers here
to the minimum the **environment needs** to perform the desired task. Therefore, it should equate to what you expect your application will consume **maximally**. 
The entry `can_use_gpu` communicates to the container whether the application can make use of an NVIDIA GPU. If set to `true`, the container will be provided with a GPU if one is available. To *require* a GPU (fail if none is available), set `min_count_required_gpus` to a value greater than zero in the `reconstruction` section (see Step 2 below). If `can_use_gpu` is `true` but `min_count_required_gpus` is zero, the application runs without GPU acceleration when no GPU is present.

### Step 4: Define the UI for your application

The `parameters` section defines the user interface of the Open Recon application inside the Scanner UI. It may be empty for applications which do not need end-user supplied parameters, but can contain up to 14 parameters which are communicated to the application at runtime using a JSON message which is sent as part of the MRD communication.

---

## The `reconstruction` Section

Now that you are familiar with the structure and information in an application specification, the next steps take a closer look at the information these sections can contain.


### Step 1: Choose your emitter and injector points

The emitter and injector define how your container connects to the ICE pipeline.
Not all combinations of allowed values are currently supported.
The three combinations are:
- emitter `raw`, injector `image`: named **raw to image** (r2i)
- emitter `raw`, injector `compleximage`: named **raw to compleximage** (r2ci)
- emitter `image`, injector `image`: named **image to image** (i2i)

        ToDo: Change your emitter to r2ci 
        and check against the schema.

### Step 2: Describe your hardware

The container may require GPUs or large amounts of memory.
Besides `can_use_gpu` set to `true`, you can indicate that an application strictly requires a GPU
by setting `min_count_required_gpus` to larger than zero. Zero indicates optional use of a GPU.
Specify the maximum amount of GPU memory your application will use via `min_required_gpu_memory` — this value becomes the guaranteed minimum allocation. The **required unit for GPU memory is MB**.

        ToDo: Change the template to indicate that your application 
        needs a GPU and check against the provided json schema.

### Step 3: Describe expectations on the environment

Some applications may require special ICE settings. E.g. in r2ci one can influence the `channel_compression` which can be turned `on` or `off` and can be set to a fixed number of channels.
Similarly, filters in readout direction can be switched off by modifying the `require_readout_filter_off` entry.

        ToDo: Set readout filters and coil compression off 
        and check against the provided json schema.

---

## The `parameter` section

Finally, we turn towards the options you have for your application to define end-user input.

### Step 1: Create a numerical parameter

A parameter is defined as a json object in the "parameters" list:
```json
{}
```
Such a parameter object always requires a `type`, `id`, `label`, `information` and a `default` value. 
The `type` refers to the type of parameter e.g. `int`, `double` for numerical values. Doubles can only be set in increments of 0.1 and numerical types also need a `unit`.
`id` is again the language-independent identifier under which your application will receive the chosen value at runtime.
`label` and `information` are the respective end-user-visible values on the user interface. The `default` value is used to fill the input field with an initial value.

        ToDo: Create a new integer user input parameter. 
        Add this under "parameters" check against the schema.

### Step 2: Create a string parameter

String parameters allow free text input and also have `type`, `id`, `label`, `information` and a `default` value. 
They can optionally be marked as `isLargeText: true` for multi-line input.

        ToDo: Create a new string user input parameter. 
        Add this under "parameters" check against the schema.

### Step 3: Create an enum parameter

Enum parameters are represented by `choice`. They allow the user to select from predefined values. They also have `type`, `id`, `label`, `information` and a `default`, but require a new list of `values`.
These values themselves are JSON objects which need an `id` and a user-facing `name`. The default value refers to the `id` of one of the elements in `values`.

        ToDo: Create a new choice user input parameter. 
        Add this under "parameters" check against the schema.

# Conclusion

After finishing these steps, you will have a fully validated application specification JSON that contains descriptive metadata, environment requirements, and user-exposed parameters. You can use the working examples in [`server/modules/`](../../server/modules) as a reference for real `appl_spec.json` files.