# -*- coding: utf-8 -*-

import logging

LOG = logging.getLogger(__name__)


def disease_entry(store, disease_id):
    """Retrieve specific info for an OMIM term at the gene level

    Args:
        store(obj): an adapter to the scout database
        disease_id(str): a disease_id

    Returns:
        omim_obj(obj): an OMIM term containing description and genes
    """

    disease_obj = store.disease_term(disease_identifier=disease_id, filter_project={})
    disease_obj["genes_complete"] = store.omim_to_genes(disease_obj)
    disease_obj["hpo_complete"] = [
        store.hpo_term(hpo_id) for hpo_id in disease_obj.get("hpo_terms", [])
    ]
    return disease_obj


def disease_terms(store):
    """Retrieve all disease terms.
    Args:
        store(adapter.MongoAdapter):  an adapter to the scout database
    Returns:
        data(dict): dict with key "terms" set to an array of all disease terms
    """

    data = {"terms": store.disease_terms(filter_project=None)}
    return data
