# Alteryx_SDK_UrlParser
Custom Alteryx SDK tool to parse URLs

## Installation
Download the yxi file and double click to install in Alteyrx. The tool will be installed in the __Parse__ category.

![alt text](https://github.com/bobpeers/Alteryx_SDK_UrlParser/blob/master/images/UrlParser_toolbar.png "Alteryx Parse Category")

## Requirements

This tool uses the standard Python libraries so no dependencies will be installed.

## Usage
This tool takes one input and required a field to be mapped to the URL that will be parsed

## Outputs
The parsed URL will be fed out along with all the input fields. The output fields are:

| Attribute | Value                              | Value if not present |
|-----------|------------------------------------|----------------------|
| protocol    | URL scheme specifier               | scheme parameter     |
| net_location    | Network location part              | empty string         |
| path      | Hierarchical path                  | empty string         |
| params    | Parameters for last path element   | empty string         |
| query     | Query component                    | empty string         |
| parsed_query    | Parsed query compenent   | empty string         |
| fragment  | Fragment identifier                | empty string         |
| hostname  | Host name (lower case)             | empty string         |
| port      | Port number as integer, if present | null                 |


## Usage
This workflow demonstrates the tool in use and the output data.

![alt text](https://github.com/bobpeers/Alteryx_SDK_UrlParser/blob/master/images/UrlParser_workflow.png "UrlParser Workflow")
