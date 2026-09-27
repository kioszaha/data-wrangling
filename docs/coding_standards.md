## Structure: Organising Folders, Files & Output 

1. Data is stored in its own folder separated by airbnb and bonds files.  

2. Our Python functions are organised on a deliverable basis. Lecture notes suggest using lots of smaller files. One python file per deliverable is sufficient because each function only serves one purpose. Functions that get reused have been placed in utils folder. e.g. sync_data.py 

3. The repository has one clear output folder that contains all the outputs from each deliverable, including csv, pdf, png, and text files. 

## Coding Practices 

Parameters are clearly defined at the start of the file with no magic numbers. Follow best practice coding conventions including uppercase variable names for constant parameters.

All our python scripts use variables to reference relative file paths in our repository instead of hard coding values.

Fixes:
1. The Christchurch Central area code (326600) was previously hardcoded in a couple places in deliverable_5.py. Replaced with a single constant variable (CHRISTCHURCH_CENTRAL_AREA_CODE) because keeps code working if the value changes in the future.

2. The R markdown code from deliveable 3 hardcoded it's output. Fixed by using the OUTPUT_DIR variable because it stays consistent with how the rest of the file handles paths.

## Code Comments 

Code comments are used to explain non-obvious choices made during development and any data caveats.
Additionally comments are used to communicate structure of deliverable tasks for tutor’s benefit. 

Reviwed comments against notes and already following recommended best practice, no changes needed. 

## Example of Sanity Check in Pipeline

In deliverable 5 we have a fetch_coodinates() function that checks the Koordinates Statistical Area 2 2026 dataset. It raises a RuntimeError or a FileNotFoundError, if either more than 5% of the data is missing or the input file is invalid.

This ensures our data for deliverable 5 is correct early in the pipeline.

## Further Cleanups 

Integrated the deliverable 3 workflow and plots that were originally built in RStudio as an R Markdown file into the Python pipeline using the rpy2 package. The subsequent graphs now correctly appear in the output folder. 