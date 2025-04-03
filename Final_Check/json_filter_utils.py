# written by Lekhraj Pandey, USD.
#**************************************#
"""
This script will reduced the size of the start and end of the ODB JSON structure.
With in start or end json, it call the following filter functions:
    1) filter_json_remove_slash_key_value
    2) filter_json_remove_system_keys
    3) filter_json_remove_legacytrigger
    4) find_and_delete_common_keys 
     Final function to do this task: filter_and_clean_json
    
In case of dumping odb_end json, After the above filter function, only those keys and values from odb_end json 
will be stored, which are different than start_odb
   Final function to do that task: find_differences_final_wrt_start_json
   
"""
#***************************************#
import json
import sys
import re

def filter_json_remove_slash_key_value(data, pattern="/key"):
    """
    Recursively removes keys from a dictionary if they contain the given pattern.

    Parameters:
    data (dict): The input dictionary to process.
    pattern (str): The substring pattern to check in keys. Default is "/key".

    Returns:
    dict: A new dictionary with keys containing the pattern removed.

    - If `data` is not a dictionary, it is returned unchanged.
    - Iterates over key-value pairs in the dictionary.
    - If a key does not contain the specified pattern:
        - If the value is a dictionary, applies the function recursively.
        - Otherwise, retains the value as is.
    """
    if not isinstance(data, dict):
        return data  # If data is not a dictionary, return as is
    
    new_dict = {}
    for k, v in data.items():
        if pattern not in k:  # Exclude keys that contain the pattern
            if isinstance(v, dict):
                new_dict[k] = filter_json_remove_slash_key_value(v, pattern)  # Recurse for nested dict
            else:
                new_dict[k] = v  # Keep the value as is
    
    return new_dict

def filter_json_remove_system_keys(data):
    """
    Modifies the input dictionary by removing specific keys from the 'System' section
    and filtering out entries containing "/last_written" in the key.

    Parameters:
    data (dict or list): The input dictionary or list of dictionaries to process.

    Returns:
    dict or list: The modified dictionary with certain 'System' keys removed, or a filtered list.

    Functionality:
    - If 'System' exists in the dictionary:
        - Defines a list of keys ('Buffers', 'Transition', 'Flush', 'Tmp') to remove.
        - Iterates through the list and removes these keys from 'System' if they are present.
    - If `data` is a list:
        - Filters out any dictionary entries where the key contains "/last_written".
    """

    # Ensure we only modify the 'System' key if it exists
    if 'System' in data:
        # List of keys to remove from 'System'
        keys_to_remove = ['Buffers', 'Transition', 'Flush', 'Tmp']
        
        # Loop through the list and remove each key from 'System' if it exists
        for key in keys_to_remove:
            data['System'].pop(key, None)

    # Filter out entries that have "/last_written" in the key
    if isinstance(data, list):  # Check if data is a list of dictionaries
        data = [entry for entry in data if "/last_written" not in entry.get("key", "")]

    return data

def filter_json_remove_legacytrigger(data):
    """
    Recursively removes keys that match the pattern "/Detectors/DetXX/Settings/LegacyTrigger".

    Parameters:
    data (dict): The input dictionary to process.

    Returns:
    dict: The modified dictionary with matching keys removed.

    Functionality:
    - Defines a helper function `recursive_trim(d)` to perform recursive key removal.
    - If the input is a dictionary:
        - Identifies keys matching the pattern "/Detectors/DetXX/Settings/LegacyTrigger".
        - Removes the identified keys.
        - Recursively processes nested dictionaries and lists.
    - Calls `recursive_trim(data)` to modify the input dictionary.
    """

    def recursive_trim(d):
        if isinstance(d, dict):
            # Identify keys matching the specific pattern
            keys_to_remove = [key for key in d if "/Detectors/Det" in key and "/Settings/LegacyTrigger" in key]
            # Remove the matching keys
            for key in keys_to_remove:
                del d[key]
            # Recursively process nested dictionaries or lists
            for key, value in d.items():
                if isinstance(value, (dict, list)):  # If the value is a dictionary or list, apply recursion
                    recursive_trim(value)

    # Call the recursive trim function on the data
    recursive_trim(data)
    
    return data

def remove_keys_ending_with_comment(data):
    """
    Recursively removes all dictionary keys that end with 'Comment', 'comment', 'Comments', or 'comments'.
    
    Parameters:
    data (dict or list): The JSON structure (dictionary or list) to process.

    Returns:
    None (modifies the input data in place).

    Functionality:
    - If `data` is a dictionary, it:
        1. Identifies keys ending with 'Comment', 'comment', 'Comments', or 'comments' using regex.
        2. Deletes those keys from the dictionary.
        3. Recursively applies the function to the remaining values (nested dictionaries or lists).
    - If `data` is a list, it:
        1. Iterates through each item and applies the function recursively.
    """

    if isinstance(data, dict):
        # Identify keys that match the regex pattern (ending with "Comment"/"comment"/etc.)
        keys_to_delete = [key for key in data if re.search(r'(Comment|comment|Comments|comments)$', key)]
        
        # Remove the identified keys from the dictionary
        for key in keys_to_delete:
            del data[key]

        # Recursively apply the function to the remaining dictionary values
        for key in list(data.keys()):  
            remove_keys_ending_with_comment(data[key])

    elif isinstance(data, list):
        # Recursively apply the function to each item in the list
        for item in data:
            remove_keys_ending_with_comment(item)


def find_readback_and_settings_paths(data, prefix=""):
    """
    Recursively finds all paths in a JSON structure that contain 'Readback' or 'Settings' in their key names.

    Parameters:
    data (dict): The input JSON structure to search.
    prefix (str): The current path of the recursive traversal.

    Returns:
    tuple: Two dictionaries, one containing Readback paths and the other containing Settings paths.

    Functionality:
    - Iterates through all keys in `data`:
        1. Constructs a full path for each key.
        2. If the value is a dictionary, recursively searches within it.
        3. If the path contains 'Readback', it is stored in `readback_paths`.
        4. If the path contains 'Settings', it is stored in `settings_paths`.
    """

    readback_paths = {}
    settings_paths = {}

    for key, value in data.items():
        # Construct the full path
        full_path = f"{prefix}/{key}" if prefix else key

        if isinstance(value, dict):
            # Recursively search inside nested dictionaries
            sub_readback, sub_settings = find_readback_and_settings_paths(value, full_path)
            readback_paths.update(sub_readback)
            settings_paths.update(sub_settings)
        else:
            # Store paths that contain 'Readback' or 'Settings'
            if "Readback" in full_path:
                readback_paths[full_path] = value
            elif "Settings" in full_path:
                settings_paths[full_path] = value

    return readback_paths, settings_paths


def delete_key_by_full_path(data, full_path):
    """
    Deletes a key from the JSON structure using its full hierarchical path.

    Parameters:
    data (dict): The JSON structure to modify.
    full_path (str): The full path of the key to be deleted (e.g., "System/Settings/Threshold").

    Returns:
    None (modifies the input data in place).

    Functionality:
    - Splits `full_path` into a list of keys.
    - Traverses through `data` to locate the parent dictionary.
    - If the last key exists in the parent dictionary, it is deleted.
    - If an empty dictionary remains, it is also removed from its parent.
    """

    keys = full_path.split("/")  # Split the full path into individual keys
    current = data
    stack = []  # Stack to keep track of traversed keys

    for key in keys[:-1]:  # Traverse until the parent dictionary
        if key in current and isinstance(current[key], dict):
            stack.append((current, key))  # Save reference to parent
            current = current[key]
        else:
            return  # Key path does not exist

    last_key = keys[-1]  # Key to be deleted

    if last_key in current:
        del current[last_key]  # Delete the key from the dictionary

    # Cleanup: remove empty dictionaries from the hierarchy
    while stack:
        parent, key = stack.pop()
        if not parent[key]:  # If the dictionary is now empty
            del parent[key]
        else:
            break  # Stop if the parent still contains other data


def extract_common_part(full_key):
    """
    Extracts the key path without 'Readback' or 'Settings'.

    Parameters:
    full_key (str): The full key path.

    Returns:
    str: The extracted path without 'Readback' or 'Settings'.

    Functionality:
    - Uses regex to identify and remove 'Readback' and 'Settings' from the path.
    - Returns the remaining portion of the key path.
    """

    pattern = re.compile(r'^(.*?)/?(Readback|Settings)/?(.*)$')
    match = pattern.match(full_key)

    if match:
        before = match.group(1)  # Part before 'Readback'/'Settings'
        after = match.group(3)   # Part after 'Readback'/'Settings'

        if before and after:
            return f"{before}/{after}"
        elif before:
            return before
        else:
            return after

    return full_key  # If no match, return the original key


def find_and_delete_common_keys(readback_dict, settings_dict, json_data):
    """
    Finds and removes identical key-value pairs from both 'Readback' and 'Settings' paths in a JSON structure.

    Parameters:
    readback_dict (dict): Dictionary containing paths and values for 'Readback' keys.
    settings_dict (dict): Dictionary containing paths and values for 'Settings' keys.
    json_data (dict): The original JSON structure.

    Returns:
    dict: The modified JSON structure with identical Readback & Settings values removed.

    Functionality:
    - Creates a mapping of common key paths from `readback_dict` and `settings_dict`.
    - Identifies keys that exist in both mappings.
    - If the values for Readback and Settings match, both keys are deleted from `json_data`.
    """

    # Create a mapping of extracted key paths to original paths
    rb_mapping = {extract_common_part(k): k for k in readback_dict}
    st_mapping = {extract_common_part(k): k for k in settings_dict}

    # Find common key paths that exist in both mappings
    common_parts = set(rb_mapping.keys()) & set(st_mapping.keys())

    for common in common_parts:
        rb_key = rb_mapping[common]  # Full path of Readback key
        st_key = st_mapping[common]  # Full path of Settings key

        # If both keys have the same value, remove them from the JSON data
        if readback_dict[rb_key] == settings_dict[st_key]:
            delete_key_by_full_path(json_data, rb_key)
            delete_key_by_full_path(json_data, st_key)

    return json_data

def find_and_delete_common_keys_with_extra_cut(readback_dict, settings_dict, json_data):
    """
    Finds and removes:
    1. Identical key-value pairs from both 'Readback' and 'Settings'.
    2. Matching values between 'path/Readback/ReadoutControl' and 'path/ReadoutControl'.

    Parameters:
    - readback_dict (dict): Dictionary containing paths and values for 'Readback' keys.
    - settings_dict (dict): Dictionary containing paths and values for 'Settings' keys.
    - json_data (dict): The original JSON structure.

    Returns:
    - dict: The modified JSON structure.
    """

    # Step 1: Remove identical Readback & Settings values
    rb_mapping = {extract_common_part(k): k for k in readback_dict}
    st_mapping = {extract_common_part(k): k for k in settings_dict}

    common_parts = set(rb_mapping.keys()) & set(st_mapping.keys())

    for common in common_parts:
        rb_key = rb_mapping[common]
        st_key = st_mapping[common]

        if readback_dict[rb_key] == settings_dict[st_key]:
            delete_key_by_full_path(json_data, rb_key)
            delete_key_by_full_path(json_data, st_key)

    # Step 2: Find matching Readback and Settings at the same depth
    rb_paths = {k.rsplit("/", 1)[0]: k for k in readback_dict}  # Remove last key part to get parent path
    st_paths = {k.rsplit("/", 1)[0]: k for k in settings_dict}

    common_parent_paths = set(rb_paths.keys()) & set(st_paths.keys())

    for parent_path in common_parent_paths:
        rb_control_path = f"{parent_path}/Readback/ReadoutControl"
        st_control_path = f"{parent_path}/ReadoutControl"

        if rb_control_path in json_data and st_control_path in json_data:
            if json_data[rb_control_path] == json_data[st_control_path]:
                delete_key_by_full_path(json_data, rb_control_path)
                delete_key_by_full_path(json_data, st_control_path)

    return json_data

def filter_and_clean_json(json_data):
    """
    Processes a JSON object by performing the following steps:

    1. Removes all keys that end with "Comment", "comment", "Comments", or "comments".
    2. Extracts paths containing "Readback" and "Settings" from the filtered JSON.
    3. Identifies and removes redundant "Readback" and "Settings" key-value pairs
       if they have identical values.
    4. Returns the cleaned JSON object.

    Parameters:
        json_data (dict): The input JSON object.

    Returns:
        dict: The cleaned JSON object after filtering.
    """
    # Convert string JSON to a dictionary if needed
    #if isinstance(json_data, str):
    #    json_data = json.loads(json_data)
    # Step 1: Normalize and filter unwanted keys from the JSON object
    json_data = filter_json_remove_slash_key_value(json_data)
    json_data = filter_json_remove_system_keys(json_data)
    json_data = filter_json_remove_legacytrigger(json_data)

    # Step 2: Remove all keys ending with "Comment"
    filtered_json = json_data.copy()
    remove_keys_ending_with_comment(filtered_json)

    # Step 3: Extract paths for "Readback" and "Settings"
    readback_paths, settings_paths = find_readback_and_settings_paths(filtered_json)

    # Step 4: Find and delete common "Readback" and "Settings" keys with identical values
    updated_json = find_and_delete_common_keys(readback_paths, settings_paths, filtered_json)
    updated_json = find_and_delete_common_keys_with_extra_cut(readback_paths, settings_paths, updated_json)
    #updated_json = json.dumps(updated_json, separators=(',', ':'), indent=None)
    #if isinstance(updated_json, str):
    #    updated_json = json.loads(updated_json)
    # Step 5: Return the cleaned JSON object
    return updated_json


def find_differences_final_wrt_start_json(start_obj, end_obj):
    """
    Compares two dictionaries (`start_obj` and `end_obj`) to identify and return the differences between them.

    This function is designed to highlight the changes, additions, and removals between two JSON-like objects.

    Parameters:
    start_obj (dict): The initial dictionary (starting state) to compare from.
    end_obj (dict): The modified dictionary (ending state) to compare against.

    Returns:
    dict: A dictionary containing the differences between `start_obj` and `end_obj`, where each key represents 
          a modified, newly added, or missing key from the `start_obj`. The values of the dictionary will be the 
          updated values from `end_obj`.

    Functionality:
    - The function first filters out certain key-value pairs from both the `start_obj` and `end_obj` using custom 
      filtering functions (`filter_json_remove_slash_key_value`, `filter_json_remove_system_keys`, and 
      `filter_json_remove_legacytrigge`) to normalize the objects.
    - It then uses a helper function `recursive_diff(start, end)` to perform a recursive comparison between the two 
      dictionaries:
        - For each key in `end_obj`, it checks:
            - If the key does not exist in `start_obj`, it is considered a new addition.
            - If the key exists in both objects and both values are dictionaries, the function recursively compares 
              their contents.
            - If the key exists in both objects and both values are lists, it compares the lists directly.
            - If the key exists in both objects but the values differ (for either dictionaries, lists, or primitive values), 
              it adds the updated value from `end_obj` to the differences.
    - The function returns a dictionary containing only the keys that have changed or been added/removed, with their 
      respective updated values.
    """
    # Normalize both start and end objects by removing unwanted key-value pairs
    start_obj = filter_json_remove_slash_key_value(start_obj)
    start_obj = filter_json_remove_system_keys(start_obj)
    start_obj = filter_json_remove_legacytrigger(start_obj)
    end_obj = filter_json_remove_slash_key_value(end_obj)
    end_obj = filter_json_remove_system_keys(end_obj)
    end_obj = filter_json_remove_legacytrigger(end_obj)

    def recursive_diff(start, end):
        """
        A recursive helper function to compare two dictionaries or lists, 
        identifying and returning differences between them.

        Parameters:
        start (dict or list): The initial object to compare.
        end (dict or list): The modified object to compare against.

        Returns:
        dict: A dictionary containing the differences (key-value pairs) 
              between `start` and `end`.
        """
        diff = {}
        for key in end.keys():
            if key not in start:
                # Key is new in end_obj
                diff[key] = end[key]
            elif isinstance(start[key], dict) and isinstance(end[key], dict):
                # Recursively compare nested dictionaries
                nested_diff = recursive_diff(start[key], end[key])
                if nested_diff:  # Only add if there are differences
                    diff[key] = nested_diff
            elif isinstance(start[key], list) and isinstance(end[key], list):
                # Compare lists directly
                if start[key] != end[key]:
                    diff[key] = end[key]
            elif start[key] != end[key]:
                # If values differ, add the updated value from end_obj
                diff[key] = end[key]
        return diff

    # Initiate recursive comparison and return the differences
    return json.dumps(recursive_diff(start_obj, end_obj), separators=(',', ':'))
