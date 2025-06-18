# No Depictor

This is a Python script that facilitates mass addition of "No" statements to [Depictor](https://hay.toolforge.org/depictor). Please use with care.

## Usage

Before running No Depictor for the first time, ensure that you have Python installed in your system and download libraries required by the tool. On Windows, you can do it by running the `install.bat` file.

Please ensure that you are logged in to Depictor in a web browser and don't logout while the script is running.

Once ready, start the tool by double-clicking the `start.bat` file. At the beginning, you will be asked for some information. Please answer the questions in terminal and confirm using Enter:

* The categories to process. You can either type the name of a Commons category or provide a path to a text file with categories. In the latter case, each category should be in a separate line (with or without the `Category:` prefix).
* The depth of the category tree to process. `0` means only subcategories directly in the input categories.
* Your username in Wikimedia projects. It could be technically any string, but it's the name which will be attributed to the decisions in Depictor.
* Value of your PHPSESSID cookie for Depictor. This script reuses the session you make interactively in your browser, so you will need to type the session id.

These information will be stored in a file, so that the next time you're running the script, you'll be able to reuse them by leaving specific inputs empty and clicking Enter.

After typing the session identifier, the script will start working. The progress will be displayed on the screen and you can terminate it anytime using Ctrl+C.
