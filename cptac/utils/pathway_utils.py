#   Copyright 2018 Samuel Payne sam_payne@byu.edu
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import pandas as pd
import numpy as np
import sys
import urllib3
import json
import requests
import webbrowser
import warnings

from cptac.exceptions import HttpResponseError, InvalidParameterError, ParameterWarning

'''
@Param protein:
    The name of the protein that you want to generate a list of interacting proteins for.

@Param number (default=25):
    The number of interacting proteins that you want to get.

@Return:
    A list of proteins known by the String api to be interacting partners with the specified protein.
    Returns None if specified protein isn't found in String database, or connection to String api fails.


This method takes as a parameter the name of a protein. It then accesses the STRING database, through
a call to their public API, and generates a list of proteins known to be interacting partners with the specified
protein. Optional second parameter is number (which by default is 25), which specifies in the API call how many
interacting partners to retrieve from the database. The list of interacting proteins is returned to the caller
as a python list.
'''

def get_interacting_proteins_string(protein, number=25):
    '''Use urllib3 to access the string database api, gather list of interacting proteins'''
    urllib3.disable_warnings()
    string_api_url = "https://string-db.org/api"
    output_format = "json"
    method = "network"

    '''Use the specified gene and homo sapiens species code'''
    my_protein = [protein]
    species = "9606"

    '''Format the api request to collect the appropriate information'''
    request_url = string_api_url + "/" + output_format + "/" + method + "?"
    request_url += "identifiers=%s" % "%0d".join(my_protein)
    request_url += "&" + "species=" + species
    request_url += "&" + "limit=" + str(number)

    '''Send a request to the API, print the response status'''
    try:
        http = urllib3.PoolManager()
        response = http.request('GET',request_url)
        '''Catch exception if it fails while accessing the api'''
    except urllib3.HTTPError as err:
        error_message = err.read()
        print("Error accessing STRING api, " , error_message)
        sys.exit()

    '''Get the data from the api response'''
    interacting_proteins = []
    if response.status == 200:
        '''Get the data from the API's response'''
        data = response.data
        y = json.loads(data)

        '''Make a list of the resulting interacting proteins'''
        for entry in y:
            if entry["preferredName_A"] not in interacting_proteins:
                interacting_proteins.append(entry["preferredName_A"])
            if entry["preferredName_B"] not in interacting_proteins:
                interacting_proteins.append(entry["preferredName_B"])

        if protein not in interacting_proteins:
            interacting_proteins.append(protein)

        return interacting_proteins

        '''If we didnt get a successful response from the api, notify the caller and return None'''
    else:
        print("\nSpecified gene was not found in String database, double check that you have it correctly!")
        return None


'''
@Param protein:
    The name of the protein that you want to generate a list of interacting proteins for.

@Param number (default=25):
    The number of interacting proteins that you want to get.

@Return:
    A list of proteins known by the biogrid api to be interacting partners with the specified protein.
    Returns None if specified protein isn't found in biogrid database, or connection to biogrid api fails.


This method takes as a parameter the name of a protein. It then accesses the biogrid database, through
a call to their public API, and generates a list of proteins known to be interacting partners with the specified
protein. Optional second parameter is number (which by default is 25), which specifies in the API call how many
interacting partners to retrieve from the database. The list of interacting proteins is returned to the caller
as a python list.
'''
def get_interacting_proteins_biogrid(protein, number=25):
    '''Store interacting proteins in a list'''
    interacting_proteins = []
    urllib3.disable_warnings()

    '''Configure url for request'''
    request_url = "https://webservice.thebiogrid.org/interactions/?searchNames=true&geneList=" + protein +"&includeInteractors=true&format=json&taxId=9606&start=0&max=" + str(number) + "&accesskey=0ff59dcf3511928e78aad499688381c9"
    try:
        '''Send request, get response'''
        http = urllib3.PoolManager()
        response = http.request('GET',request_url)

        '''If response was successful'''
        if response.status == 200:
            '''Get the data from the API's response'''
            data = response.data
            y = json.loads(data)

            '''Add name of each protein to list of interacting proteins'''
            for entry in y:
                if y[entry]['OFFICIAL_SYMBOL_A'] not in interacting_proteins:
                    interacting_proteins.append(y[entry]['OFFICIAL_SYMBOL_A'])

            '''Return this list to caller'''
            return interacting_proteins

        else:
            '''If response was not successful, notify caller of error, return None'''
            print("Error accessing api!")
            return None

        '''Catch exception, notify caller of error, return None'''
    except Exception as err:
        print("Error accessing api, " , err)
        return None


'''
@Param protein:
    The name of the protein that you want to generate a list of interacting proteins for.

@Param number (default=25):
    The number of interacting proteins that you want to get from both STRING and BioGrid(used by uniprot). This
    number of proteins will be generated by both String and BioGrid, and the two will be combined. The actual number of
    proteins in the list returned by this method will be between the number specified and 2 times the number specified,
    depending on how many of the interacting proteins the two APIs 'agree' on.

@Return:
    A list of proteins known by the String and BioGrid APIs to be interacting partners with the specified protein.
    Returns None if specified protein isn't found in either database, or both API calls fail.


This method takes as a parameter the name of a protein. It then accesses the STRING and BioGrid databases, through
a call to their public API, and generates a list of proteins known to be interacting partners with the specified
protein. Optional second parameter is number (which by default is 25), which specifies in the API call how many
interacting partners to retrieve from the database. The list of interacting proteins is returned to the caller
as a python list.
'''
def get_interacting_proteins(protein, number=25):
    string_list = get_interacting_proteins_string(protein, number)
    biogrid_list = get_interacting_proteins_biogrid(protein, number)

    if string_list == None and biogrid_list == None:
        return None

    else:
        interacting_proteins = []
        for prot in string_list:
            if prot not in interacting_proteins:
                interacting_proteins.append(prot)
        for prot in biogrid_list:
            if prot not in interacting_proteins:
                interacting_proteins.append(prot)

        return interacting_proteins

'''
@Param protein:
    The name of the protein that you want to generate a list of interacting proteins for.

@Return:
    A list of proteins which are interacting partners with the specified protein, according to the bioplex data table.
    Returns None if specified protein isn't found, or no interacting partners are found.

This method takes as a parameter the name of a protein. It then accesses the bioplex data table and returns a list of any protein found to be an interacting partner to the given protein.
'''

def get_interacting_proteins_bioplex(protein, secondary_interactions=False):
    path_here = os.path.abspath(os.path.dirname(__file__))
    file_name = "BioPlex_interactionList_v4a.tsv"
    file_path = os.path.join(path_here, file_name)

    bioplex_interactions = pd.read_csv(file_path, sep='\t')

    A_df = bioplex_interactions.loc[bioplex_interactions['SymbolA'] == protein]
    B_df = bioplex_interactions.loc[bioplex_interactions['SymbolB'] == protein]

    A_interactions = list(A_df['SymbolB'])
    B_interactions = list(B_df['SymbolA'])

    all_interactions = list(set(A_interactions + B_interactions))

    if secondary_interactions:
        secondary_interactions_list = []
        for interaction in all_interactions:
            secondary = get_interacting_proteins_bioplex(interaction, False)
            for si in secondary:
                secondary_interactions_list.append(si)

        for asi in secondary_interactions_list:
            if asi not in all_interactions:
                all_interactions.append(asi)

    if len(all_interactions) > 0:
        return all_interactions
    else:
        return None

"""
@param protein:
	String. The name of the protein
@Return:
	A list of proteins known by the most recent WikiPathways download to be interacting parters with the specified protein.
	Returns None if specified protein is not found in the WikiPathways dataframe (which was intersected with Uniprot).

This function takes a path to WikiPathways Dataframe file and protein name and returns a list of all the proteins that interact with it, using the pathways from the WikiPathways relsease file.
This function loads the WikiPathways dataframe, and iterates through the row labelled with that protein name, return every protein in a pathway that also contains that protein.
"""

def get_interacting_proteins_wikipathways(protein):
    path_here = os.path.abspath(os.path.dirname(__file__))
    file_name = "WikiPathwaysDataframe.tsv"
    file_path = os.path.join(path_here, file_name)
    proteinName = protein

    df =pd.read_csv(file_path, sep="\t", index_col=False)
    df.set_index("Unnamed: 0", inplace=True)
    if (proteinName in df.index):
    	row = df.loc[proteinName]
    	filtered_df = df.loc[:, row.values.tolist()]
    	def has_true(values):
    		for val in values:
    			if val == True:
    				return True
    		return False
    	filtered_df_final = filtered_df.loc[filtered_df.apply(lambda row: has_true(row.values.tolist()), axis=1), :]
    	return filtered_df_final.index.tolist()
    return list()  # The protein was not found.

'''
@ Param: protein:
	The name of the protein that you want to generate the list of pathways for
@ Return:
	A list of pathways the given protein is involved in.

Uses the WikiPathwaysDataframe to find the pathways the given protein is involved in.
'''
def get_protein_pathways(protein):
    path_here = os.path.abspath(os.path.dirname(__file__))
    file_name = "WikiPathwaysDataframe.tsv"
    file_path = os.path.join(path_here, file_name)

    proteinName = protein
    df =pd.read_csv(file_path, sep="\t", index_col=False)
    df.set_index("Unnamed: 0", inplace=True)
    if (proteinName in df.index):
    	row = df.loc[proteinName]
    	filtered_df = df.loc[:, row.values.tolist()]
    	return list(filtered_df.columns)
    return list()  # The protein was not found.


'''
@ Return:
	A list of all the possible pathways
Uses the WikipathwaysDataFrame to return a list of all the possible pathways found.
'''
def list_pathways():
    path_here = os.path.abspath(os.path.dirname(__file__))
    file_name = "WikiPathwaysDataframe.tsv"
    file_path = os.path.join(path_here, file_name)

    df =pd.read_csv(file_path, sep="\t", index_col=False)
    df.set_index("Unnamed: 0", inplace=True)
    return list(df.columns)

'''
@ Param pathway:
	String. The name of a pathway
@ Return:
	A list of all the proteins involved in the given pathway
Uses the WikiPathwaysDataFrame to find all the genes involved in the given pathway.
'''
def get_proteins_in_pathway(pathway):
    path_here = os.path.abspath(os.path.dirname(__file__))
    file_name = "WikiPathwaysDataframe.tsv"
    file_path = os.path.join(path_here, file_name)

    df =pd.read_csv(file_path, sep="\t", index_col=False)
    df.set_index("Unnamed: 0", inplace=True)
    if (pathway in df.columns):
    	col = df[pathway]
    	filtered_df = df.loc[col, :]
    	return list(filtered_df.index)
    return list()  # The protein was not found.

def reactome_pathway_overlay(df, pathway, open_browser=True, export_path=None, image_format="png", display_col_idx=0, diagram_colors="Modern", overlay_colors="Standard", quality=7):
    """Visualize numerical data (e.g. protein expression) on a Reactome pathway diagram, with each node's color corresponding to the expression value provided for that molecule.

    Parameters:
    df (pandas.DataFrame or pandas.Series): The data you want to overlay. Each row corresponds to a particular gene/protein/etc, and each column is expression or other data for a sample or aggregate. Index must be unique identifiers. Multiple data columns allowed. All dtypes must be numeric. No NaNs allowed--we want the user to decide how to handle missing values, depending on the context of their analysis.
    pathway (str): The Reactome ID for the pathway you want to overlay the data on, e.g. "R-HSA-73929".
    open_browser (bool, optional): Whether to automatically open the diagram in a new web browser tab. Default True.
    export_path (str, optional): A string providing a path to export the diagram to. Must end in a file name with the same extension as the "image_format" parameter. Default None causes no figure to be exported.
    image_format (str, optional): If export_path is not none, this specifies the format to export the diagram to. Options are "png", "gif", "svg", "jpg", "jpeg", or "pptx". Must match the file extension in the export path. If you're creating a gif and you want more than one column's data to be included in the image, make sure to pass None to the display_col_idx parameter. Default "png".
    display_col_idx (int, optional): If export_path is not none, this specifies which column in the dataframe to overlay expression data from. Must be a valid column index for the given table, or None. None will cause the first column to be displayed, unless you're creating a gif, in which case it will cause all columns to be included in the gif. Default None.
    diagram_colors (str, optional): If export_path is not none, this specifies the Reactome color scheme to use for the underlying diagram. Options are "Modern" or "Standard". Default "Modern".
    overlay_colors (str, optional): If export_path is not none, this specifies the Reactome color scheme to use for the data overlay. Options are "Standard", "Strosobar", or "Copper Plus". Default "Standard".
    quality (int, optional): If export_path is not none, this specifies what relative quality to export the image at. Must be between 1 and 10 inclusive. Default 7.

    Returns:
    str: If export_path is None, returns URL to diagram with data overlaid in Reactome Pathway Browser. Otherwise returns the path the image was exported to.
    """
    # If they gave us a series, make it a dataframe
    if isinstance(df, pd.Series):
        if df.name is None:
            df.name = "data"
        df = pd.DataFrame(df)

    # Parameter checking
    if export_path is not None:

        if image_format not in ("png", "gif", "svg", "jpg", "jpeg", "pptx"):
            raise InvalidParameterError(f"Invalid value for 'image_format' parameter. Valid options are 'png', 'gif', 'svg', 'jpg', 'jpeg', or 'pptx'. You passed '{image_format}'.")

        if display_col_idx is None:
            display_col_idx = ""        
        elif display_col_idx not in range(0, df.shape[1]):
            raise InvalidParameterError(f"Invalid value for 'display_col_idx' parameter. Must be either None, or an int between 0 and one less than the number of columns in df (which is {df.shape[1] - 1} for this df), inclusive. You passed {display_col_idx}.")

        if diagram_colors not in ("Modern", "Standard"):
            raise InvalidParameterError(f"Invalid value for 'diagram_colors' parameter. Valid options are 'Modern' or 'Standard'. You passed '{diagram_colors}'.")

        if overlay_colors not in ("Standard", "Strosobar", "Copper Plus"):
            raise InvalidParameterError(f"Invalid value for 'overlay_colors' parameter. Valid options are 'Standard', 'Strosobar', or 'Copper Plus'. You passed '{overlay_colors}'.")

        if quality not in range(1, 11):
            raise InvalidParameterError(f"Invalid value for 'quality' parameter. Must be an int between 1 and 10 inclusive. You passed {quality}.")

        if image_format != export_path.split('.')[-1]:
            raise InvalidParameterError(f"The file extension in the 'export_path' parameter must match the 'image_format' parameter. For the image_format parameter, you passed '{image_format}'. The extension at the end of your export path was '{export_path.split('.')[-1]}'.")

        if export_path[:2] == "~/":
            raise InvalidParameterError("The export path you provided appeared to start with a reference to the user home directory. To avoid confusion, this function will not expand that reference. Please provide a full path instead.")

    # The identifier series (the index) needs to have a name starting with "#"
    if df.index.name is None:
        df.index.name = "#identifier"
    elif not df.index.name.startswith("#"):
        df.index.name = "#" + df.index.name

    # Take care of NaNs
    df = df.astype(str) # This represents NaNs as 'nan', which Reactome is OK with

    # Get the df as a tab-separated string
    df_str = df.to_csv(sep='\t')

    # Post the data to the Reactome analysis service
    analysis_url = "https://reactome.org/AnalysisService/identifiers/projection"
    headers = {"Content-Type": "text/plain"}
    view_resp = requests.post(analysis_url, headers=headers, data=df_str)

    # Check that the response came back good
    if view_resp.status_code != requests.codes.ok:
        raise HttpResponseError(f"Submitting your data for analysis returned an HTTP status {view_resp.status_code}. The content returned from the request may be helpful:\n{view_resp.content.decode('utf-8')}")    

    # Get the token for accessing the analysis results
    token = view_resp.json()["summary"]["token"]

    # Use the token and the pathway ID to open the pathway diagram with the data overlaid in the Reactome Pathway Browser
    viewer_url = f"https://reactome.org/PathwayBrowser/#/{pathway}&DTAB=AN&ANALYSIS={token}"
    if open_browser:
        webbrowser.open(viewer_url)

    if export_path is not None:

        # Get the diagram
        export_url = f"https://reactome.org/ContentService/exporter/diagram/{pathway}.{image_format}?token={token}&resource=TOTAL&diagramProfile={diagram_colors}&analysisProfile={overlay_colors}&expColumn={display_col_idx}&quality={quality}"
        export_resp = requests.get(export_url)

        # Check that the response came back good
        if export_resp.status_code != requests.codes.ok:
            raise HttpResponseError(f"Submitting your data for analysis returned an HTTP status {export_resp.status_code}. The content returned from the request may be helpful:\n{export_resp.content.decode('utf-8')}")    

        # Save the image
        with open(export_path, 'wb') as dest:
            dest.write(export_resp.content)

    if export_path is None:
        return viewer_url
    else:
        return export_path


def search_reactome_pathways_with_proteins(ids, resource="UniProt", quiet=False):
    """Query the Reactome REST API to find Reactome pathways containing a particular gene or protein.

    Parameters:
    ids (str or list of str): The id(s) to look for matches to.
    resource (str, optional): The database the identifier(s) come from. Default is UniProt. Other options include HGNC, Ensembl, and GO. For more options, consult <https://reactome.org/content/schema/objects/ReferenceDatabase>.
    quiet (bool, optional): Whether to suppress warnings issued when identifiers are not found. Default False.

    Returns:
    pandas.DataFrame: A table of pathways containing the given genes or proteins, with pathway names and their Reactome identifiers (the latter are needed for the pathway_overlay function).
    """
    # Process string input
    if isinstance(ids, str):
        ids = [ids]

    # Set headers and params
    headers = {"accept": "application/json"}
    params = {"species": "Homo sapiens"}

    # Loop over ids and get the interacting pathways
    all_pathway_df = pd.DataFrame()
    for id in ids:
        url = f"https://reactome.org/ContentService/data/mapping/{resource}/{id}/pathways"
        resp = requests.get(url, headers=headers, params=params)

        # Check that the response came back good
        if resp.status_code == 404:
            try:
                msg = resp.json()["messages"]
            except (json.JSONDecodeError, KeyError):
                raise HttpResponseError(f"Your query returned an HTTP status {resp.status_code}. The content returned from the request may be helpful:\n{resp.content.decode('utf-8')}") from None
            else:
                if not quiet:
                    warnings.warn(f"The query for '{id}' returned HTTP 404 (not found). You may have mistyped the gene/protein ID or the resource name. The server gave the following message: {msg}", ParameterWarning, stacklevel=2)
                continue
        elif resp.status_code != requests.codes.ok:
            raise HttpResponseError(f"Your query returned an HTTP status {resp.status_code}. The content returned from the request may be helpful:\n{resp.content.decode('utf-8')}")

        # Parse out pathway IDs and names
        pathway_dict = resp.json()
        names = []
        ids = []
        for pathway in pathway_dict:
            names.append(pathway["displayName"])
            ids.append(pathway["stId"])

        pathway_df = pd.DataFrame({"id": id, "pathway": names, "pathway_id": ids})
        pathway_df = pathway_df.sort_values(by="pathway_id")
        all_pathway_df = all_pathway_df.append(pathway_df)

    all_pathway_df = all_pathway_df.reset_index(drop=True)
    return all_pathway_df

def search_reactome_proteins_in_pathways(pathway_ids, quiet=False):
    """Query the Reactome REST API to get a list of proteins contained in a particular pathway.

    Parameters:
    pathway_id (str): The pathway to get the contained proteins for.

    Returns:
    list: The proteins contained in the pathway.
    """
    # Process string input
    if isinstance(pathway_ids, str):
        pathway_ids = [pathway_ids]

    # Set headers and url
    headers = {"accept": "application/json"}

    # Loop over ids and get the interacting pathways
    all_pathway_df = pd.DataFrame()
    for pathway_id in pathway_ids:

        # Send the request
        url = f"https://reactome.org/ContentService/data/participants/{pathway_id}"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 404 or (resp.status_code == requests.codes.ok and (len(resp.content.decode("utf-8")) == 0 or len(resp.json()) == 0)):
            if not quiet:
                warnings.warn(f"The query for '{pathway_id}' found no results. You may have mistyped the pathway ID.", ParameterWarning, stacklevel=2)
            continue
        elif resp.status_code != requests.codes.ok:
            raise HttpResponseError(f"Your query returned an HTTP status {resp.status_code}. The content returned from the request may be helpful:\n{resp.content.decode('utf-8')}")

        # Parse all the proteins/genes out of the response
        all_members = resp.content.decode("utf-8").split('"')
        member_proteins = [member.split(" ")[1] for member in all_members if member.startswith("UniProt")]

        pathway_df = pd.DataFrame({"pathway_id": pathway_id, "member": member_proteins})
        pathway_df = pathway_df.sort_values(by="member")
        all_pathway_df = all_pathway_df.append(pathway_df)

    all_pathway_df = all_pathway_df.drop_duplicates(keep="first")
    all_pathway_df = all_pathway_df.reset_index(drop=True)
    return all_pathway_df
