# -*- coding: utf-8 -*-
import pytest
import logging
import datetime

from scout.utils.handle import get_file_handle

from vcf_parser import VCFParser
import yaml
import pymongo

# Adapter stuff
from mongomock import MongoClient
from scout.adapter.mongo import MongoAdapter as PymongoAdapter
# from scout.server.app import create_app

from scout.parse.case import parse_case
from scout.parse.panel import parse_gene_panel
from scout.parse.variant import parse_variant
from scout.parse.hgnc import parse_hgnc_genes
from scout.parse.ensembl import parse_ensembl_transcripts
from scout.parse.exac import parse_exac_genes
from scout.parse.hpo import (parse_hpo_phenotypes, parse_hpo_genes, parse_hpo_diseases)

from scout.utils.link import link_genes
from scout.log import init_log
from scout.build import (build_institute, build_case, build_panel, build_variant)
from scout.load import (load_hgnc_genes, load_panel)
from scout.load.hpo import load_hpo

DATABASE = 'testdb'

root_logger = logging.getLogger()
init_log(root_logger, loglevel='INFO')
logger = logging.getLogger(__name__)

# Variant and load files:
vcf_research_file = "tests/fixtures/643594.research.vcf"
sv_research_path = "tests/fixtures/1.SV.vcf"
vcf_clinical_file = "tests/fixtures/643594.clinical.vcf"
sv_clinical_path = "tests/fixtures/643594.clinical.SV.vcf"
ped_path = "tests/fixtures/643594.ped"
scout_yaml_config = 'tests/fixtures/643594.config.yaml'

# Panel file
panel_1_path = "tests/fixtures/gene_lists/panel_1.txt"
madeline_file = "tests/fixtures/madeline.xml"

# Resource files
hgnc_path = "tests/fixtures/resources/hgnc_reduced_set.txt"
ensembl_transcript_path = "tests/fixtures/resources/ensembl_transcripts_reduced.txt"
exac_genes_path = "tests/fixtures/resources/forweb_cleaned_exac_r03_march16_z_data_pLI_reduced.txt"
hpo_genes_path = "tests/fixtures/resources/ALL_SOURCES_ALL_FREQUENCIES_genes_to_phenotype_reduced.txt"
hpo_terms_path = "tests/fixtures/resources/ALL_SOURCES_ALL_FREQUENCIES_phenotype_to_genes_reduced.txt"
hpo_disease_path = "tests/fixtures/resources/diseases_to_genes.txt"
mim2gene_path = "tests/fixtures/resources/mim2gene_reduced.txt"
genemap_path = "tests/fixtures/resources/genemap2_reduced.txt"
mimtitles_path = "tests/fixtures/resources/mimTitles_reduced.txt"


# @pytest.fixture
# def app():
#     app = create_app(config=dict(DEBUG_TB_ENABLED=False, MONGO_PORT = 27017, MONGO_DBNAME = 'variantDatabase'))
#     return app

##################### Gene fixtures #####################

@pytest.fixture
def test_transcript(request):
    transcript = {
        'ensembl_transcript_id': 'enst1', # required
        'refseq_id': 'NM1',
        'start': 10, # required
        'end': 100, # required
        'is_primary': True,
    }
    return transcript

@pytest.fixture
def test_gene(request, test_transcript):
    gene = {
        # This is the hgnc id, required:
        'hgnc_id': 1,
        # The primary symbol, required
        'hgnc_symbol': 'test',
        'ensembl_id': 'ensembl1', # required
        'build': '37', # '37' or '38', defaults to '37', required

        'chromosome': 1, # required
        'start': 10, # required
        'end': 100, # required

        'description': 'A gene', # Gene description
        'aliases': ['test'], # Gene symbol aliases, includes hgnc_symbol, str
        'entrez_id': 1,
        'omim_id': 1,
        'pli_score': 1.0,
        'primary_transcripts': ['NM1'], # List of refseq transcripts (str)
        'ucsc_id': '1',
        'uniprot_ids': ['1'], # List of str
        'vega_id': '1',
        'transcripts': [test_transcript], # List of hgnc_transcript
    }
    return gene


@pytest.fixture
def genes(request, transcripts_file, hgnc_file, exac_file,
          mim2gene_file, genemap_file, hpo_genes_file):
    """Get a dictionary with the linked genes"""
    print('')
    transcripts_handle = get_file_handle(transcripts_file)
    hgnc_handle = get_file_handle(hgnc_file)
    exac_handle = get_file_handle(exac_file)
    mim2gene_handle = get_file_handle(mim2gene_file)
    genemap_handle = get_file_handle(genemap_file)
    hpo_genes_handle =  get_file_handle(hpo_genes_file)
    
    gene_dict = link_genes(
        ensembl_lines=transcripts_handle,
        hgnc_lines=hgnc_handle,
        exac_lines=exac_handle,
        mim2gene_lines=mim2gene_handle,
        genemap_lines=genemap_handle,
        hpo_lines=hpo_genes_handle
    )

    return gene_dict

#############################################################
################# Hpo terms fixtures ########################
#############################################################
@pytest.fixture
def hpo_terms_handle(request, hpo_terms_file):
    """Get a file handle to a hpo terms file"""
    print('')
    hpo_lines = get_file_handle(hpo_terms_file)
    return hpo_lines

@pytest.fixture
def hpo_terms(request, hpo_terms_file):
    """Get a dictionary with the hpo terms"""
    print('')
    hpo_terms_handle = get_file_handle(hpo_terms_file)
    return parse_hpo_phenotypes(hpo_terms_handle)

@pytest.fixture
def hpo_disease_handle(request, hpo_disease_file):
    """Get a file handle to a hpo disease file"""
    print('')
    return get_file_handle(hpo_disease_file)

@pytest.fixture
def hpo_diseases(request, hpo_disease_file):
    """Get a file handle to a hpo disease file"""
    print('')
    hpo_disease_handle = get_file_handle(hpo_disease_file)
    diseases = parse_hpo_diseases(hpo_disease_handle)
    return diseases

#############################################################
##################### Case fixtures #########################
#############################################################
@pytest.fixture(scope='function')
def ped_lines(request, scout_config):
    """Get the lines for a case"""
    case_lines = [
        "#Family ID	Individual ID	Paternal ID	Maternal ID	Sex	Phenotype",
        "643594	ADM1059A1	0	0	1	1",
        "643594	ADM1059A2	ADM1059A1	ADM1059A3	1	2",
        "643594	ADM1059A3	0	0	2	1",
        ]
    return case_lines


@pytest.fixture(scope='function')
def case_lines(request, scout_config):
    """Get the lines for a case"""
    case = parse_case(scout_config)
    return case


@pytest.fixture(scope='function')
def parsed_case(request, scout_config):
    """Get the lines for a case"""
    case = parse_case(scout_config)
    return case

@pytest.fixture(scope='function')
def case_obj(request, parsed_case, panel_database):
    adapter = panel_database
    logger.info("Create a case obj")
    case = build_case(parsed_case, adapter)
    return case


#############################################################
##################### Institute fixtures ####################
#############################################################
@pytest.fixture(scope='function')
def parsed_institute(request):
    print('')
    institute = {
        'institute_id': 'cust000',
        'display_name': 'test_institute',
        'sanger_recipients': ['john@doe.com']
    }

    return institute


@pytest.fixture(scope='function')
def institute_obj(request, parsed_institute):
    print('')
    logger.info('Building a institute')
    institute = build_institute(
        internal_id=parsed_institute['institute_id'],
        display_name=parsed_institute['display_name'],
        sanger_recipients=parsed_institute['sanger_recipients'],
    )
    return institute

#############################################################
##################### User fixtures #########################
#############################################################
@pytest.fixture(scope='function')
def parsed_user(request, institute_obj):
    """Return user info"""
    user_info = {
        'email': 'john@doe.com',
        'name': 'John Doe',
        'location': None,
        'institutes': [institute_obj['internal_id']],
        'roles': ['admin']
    }
    return user_info


@pytest.fixture(scope='function')
def user_obj(request, parsed_user):
    """Return a User object"""
    return parsed_user


#############################################################
##################### Adapter fixtures #####################
#############################################################

@pytest.fixture(scope='function')
def database_name(request):
    """Get the name of the test database"""
    return DATABASE

@pytest.fixture(scope='function')
def pymongo_client(request):
    """Get a client to the mongo database"""

    logger.info("Get a mongomock client")
    start_time = datetime.datetime.now()
    mock_client = MongoClient()

    def teardown():
        print('\n')
        logger.info("Deleting database")
        mock_client.drop_database(DATABASE)
        logger.info("Database deleted")
        logger.info("Time to run test:{}".format(datetime.datetime.now()-start_time))

    request.addfinalizer(teardown)

    return mock_client

@pytest.fixture(scope='function')
def real_pymongo_client(request):
    """Get a client to the mongo database"""

    logger.info("Get a mongomock client")
    start_time = datetime.datetime.now()
    mongo_client = pymongo.MongoClient()

    def teardown():
        print('\n')
        logger.info("Deleting database")
        mongo_client.drop_database(DATABASE)
        logger.info("Database deleted")
        logger.info("Time to run test:{}".format(datetime.datetime.now()-start_time))

    request.addfinalizer(teardown)

    return mongo_client

@pytest.fixture(scope='function')
def real_adapter(request, real_pymongo_client):
    """Get an adapter connected to mongo database"""
    logger.info("Connecting to database...")
    mongo_client = real_pymongo_client

    database = mongo_client[DATABASE]
    mongo_adapter = PymongoAdapter(database)

    # logger.info("Establish a mongoengine connection")
    # connect(DATABASE)

    logger.info("Connected to database")

    return mongo_adapter


@pytest.fixture(scope='function')
def adapter(request, pymongo_client):
    """Get an adapter connected to mongom database"""
    logger.info("Connecting to database...")
    mongo_client = pymongo_client

    database = mongo_client[DATABASE]
    mongo_adapter = PymongoAdapter(database)

    # logger.info("Establish a mongoengine connection")
    # connect(DATABASE)

    logger.info("Connected to database")

    return mongo_adapter

@pytest.fixture(scope='function')
def institute_database(request, adapter, institute_obj, user_obj):
    "Returns an adapter to a database populated with institute"
    adapter.add_institute(institute_obj)
    adapter.add_user(user_obj)

    return adapter

@pytest.fixture(scope='function')
def gene_database(request, institute_database, genes):
    "Returns an adapter to a database populated with user, institute and case"
    adapter = institute_database
    load_hgnc_genes(adapter, genes)
    
    logger.info("Creating index on hgnc collection")
    adapter.hgnc_collection.create_index([('build', pymongo.ASCENDING),
                                          ('hgnc_symbol', pymongo.ASCENDING)])
    logger.info("Index done")
    

    return adapter

@pytest.fixture(scope='function')
def hpo_database(request, gene_database, hpo_terms_handle, genemap_handle):
    "Returns an adapter to a database populated with hpo terms"
    adapter = gene_database

    load_hpo(
        adapter=gene_database,
        hpo_lines=hpo_terms_handle,
        disease_lines=genemap_handle
    )

    return adapter


@pytest.fixture(scope='function')
def panel_database(request, gene_database, panel_info):
    "Returns an adapter to a database populated with user, institute and case"
    adapter = gene_database
    logger.info("Creating a panel adapter")
    load_panel(
        adapter=adapter,
        panel_info=panel_info
    )

    return adapter

@pytest.fixture(scope='function')
def case_database(request, institute_database, case_obj):
    "Returns an adapter to a database populated with institute, user and case"
    adapter = institute_database

    adapter.add_case(case_obj)

    return adapter

@pytest.fixture(scope='function')
def populated_database(request, panel_database, institute_obj, parsed_user, case_obj):
    "Returns an adapter to a database populated with user, institute case, genes, panels"
    adapter = panel_database

    adapter.add_case(case_obj)

    return adapter


@pytest.fixture(scope='function')
def variant_database(request, populated_database, variant_objs, sv_variant_objs):
    """Returns an adapter to a database populated with user, institute, case
       and variants"""
    adapter = populated_database
    # Load variants
    for variant in variant_objs:
        adapter.load_variant(variant)

    # # Load sv variants
    # for variant in sv_variant_objs:
    #     adapter.load_variant(variant)

    return adapter

@pytest.fixture(scope='function')
def sv_database(request, populated_database, variant_objs, sv_variant_objs):
    """Returns an adapter to a database populated with user, institute, case
       and variants"""
    adapter = populated_database

    # Load sv variants
    for variant in sv_variant_objs:
        adapter.load_variant(variant)

    return adapter


#############################################################
##################### Panel fixtures #####################
#############################################################
@pytest.fixture(scope='function')
def panel_info(request):
    "Return one panel info as specified in tests/fixtures/config1.ini"
    panel = {
            'date': datetime.datetime.now(),
            'file': panel_1_path,
            'type': 'clinical',
            'institute': 'cust000',
            'version': '1.0',
            'panel_name': 'panel1',
            'full_name': 'Test panel'
        }
    return panel


@pytest.fixture(scope='function')
def parsed_panel(request, panel_info):
    """docstring for parsed_panels"""
    panel = parse_gene_panel(panel_info)

    return panel


@pytest.fixture(scope='function')
def panel_obj(request, parsed_panel, gene_database):
    """docstring for parsed_panels"""
    panel = build_panel(parsed_panel, gene_database)

    return panel

@pytest.fixture(scope='function')
def gene_panels(request, parsed_case):
    """Return a list with the gene panels of parsed case"""
    panels = parsed_case['gene_panels']

    return panels

@pytest.fixture(scope='function')
def default_panels(request, parsed_case):
    """Return a list with the gene panels of parsed case"""
    panels = parsed_case['default_panels']

    return panels

#############################################################
##################### Variant fixtures #####################
#############################################################
@pytest.fixture(scope='function')
def basic_variant_dict(request):
    """Return a variant dict with the required information"""
    variant = {
        'CHROM': '1',
        'ID': '.',
        'POS': '10',
        'REF': 'A',
        'ALT': 'C',
        'QUAL': '100',
        'FILTER': 'PASS',
        'FORMAT': 'GT',
        'INFO': '.',
        'info_dict':{},
    }
    return variant

@pytest.fixture(scope='function')
def one_variant(request, variant_clinical_file):
    logger.info("Return one parsed variant")
    variant_parser = VCFParser(infile=variant_clinical_file)

    for variant in variant_parser:
        break

    return variant

@pytest.fixture(scope='function')
def one_sv_variant(request, sv_clinical_file):
    logger.info("Return one parsed SV variant")
    variant_parser = VCFParser(infile=sv_clinical_file)

    for variant in variant_parser:
        break

    return variant

@pytest.fixture(scope='function')
def rank_results_header(request, variant_clinical_file):
    logger.info("Return a VCF parser with one variant")
    variant = VCFParser(infile=variant_clinical_file)
    rank_results = []
    for info_line in variant.metadata.info_lines:
        if info_line['ID'] == 'RankResult':
            rank_results = info_line['Description'].split('|')

    return rank_results

@pytest.fixture(scope='function')
def sv_variants(request, sv_clinical_file):
    logger.info("Return a VCF parser many svs")
    variants = VCFParser(infile=sv_clinical_file)
    return variants

@pytest.fixture(scope='function')
def variants(request, variant_clinical_file):
    logger.info("Return a VCF parser many svs")
    variants = VCFParser(infile=variant_clinical_file)
    return variants

@pytest.fixture(scope='function')
def parsed_variant(request, one_variant, parsed_case):
    """Return a parsed variant"""
    print('')
    variant_dict = parse_variant(one_variant, parsed_case)
    return variant_dict

@pytest.fixture(scope='function')
def variant_obj(request, parsed_variant, populated_database):
    """Return a variant object"""
    print('')
    institute_id = 'cust000'
    institute_obj = populated_database.institute(institute_id=institute_id)
    variant = build_variant(parsed_variant, institute_id=institute_obj['internal_id'])
    return variant

@pytest.fixture(scope='function')
def parsed_variant():
    """Return variant information for a parsed variant with minimal information"""
    variant = {'alternative': 'C',
            'callers': {
                'freebayes': None, 
                'gatk': None, 
                'samtools': None
            },
            'case_id': 'cust000-643594',
            'category': 'snv',
            'chromosome': '2',
            'clnsig': [],
            'compounds': [],
            'conservation': {'gerp': [], 'phast': [], 'phylop': []},
            'dbsnp_id': None,
            'end': 176968945,
            'filters': ['PASS'],
            'frequencies': {
                'exac': None,
                'exac_max': None,
                'thousand_g': None,
                'thousand_g_left': None,
                'thousand_g_max': None,
                'thousand_g_right': None},
            'genes': [],
            'genetic_models': [],
            'hgnc_ids': [],
            'ids': {'display_name': '1_10_A_C_clinical',
                    'document_id': 'a1f1d2ac588dae7883f474d41cfb34b8',
                    'simple_id': '1_10_A_C',
                    'variant_id': 'e8e33544a4745f8f5a09c5dea3b0dbe4'},
            'length': 1,
            'local_obs_hom_old': None,
            'local_obs_old': None,
            'mate_id': None,
            'position': 176968944,
            'quality': 10.0,
            'rank_score': 0.0,
            'reference': 'A',
            'samples': [{'alt_depth': -1,
                         'display_name': 'NA12882',
                         'genotype_call': None,
                         'genotype_quality': None,
                         'individual_id': 'ADM1059A2',
                         'read_depth': None,
                         'ref_depth': -1},
                        {'alt_depth': -1,
                         'display_name': 'NA12877',
                         'genotype_call': None,
                         'genotype_quality': None,
                         'individual_id': 'ADM1059A1',
                         'read_depth': None,
                         'ref_depth': -1},
                        {'alt_depth': -1,
                         'display_name': 'NA12878',
                         'genotype_call': None,
                         'genotype_quality': None,
                         'individual_id': 'ADM1059A3',
                         'read_depth': None,
                         'ref_depth': -1}],
            'sub_category': 'snv',
            'variant_type': 'clinical'}
    return variant

@pytest.fixture(scope='function')
def parsed_sv_variant(request, one_sv_variant, parsed_case):
    """Return a parsed variant"""
    print('')
    variant_dict = parse_variant(one_sv_variant, parsed_case)
    return variant_dict

@pytest.fixture(scope='function')
def parsed_variants(request, variants, parsed_case):
    """Get a generator with parsed variants"""
    print('')
    return (parse_variant(variant, parsed_case) for variant in variants)

@pytest.fixture(scope='function')
def parsed_sv_variants(request, sv_variants, parsed_case):
    """Get a generator with parsed variants"""
    print('')
    return (parse_variant(variant, parsed_case) for variant in sv_variants)

@pytest.fixture(scope='function')
def variant_objs(request, parsed_variants, institute_obj):
    """Get a generator with parsed variants"""
    print('')
    return (build_variant(variant, institute_obj)
            for variant in parsed_variants)

@pytest.fixture(scope='function')
def sv_variant_objs(request, parsed_sv_variants, institute_obj):
    """Get a generator with parsed variants"""
    print('')
    return (build_variant(variant, institute_obj)
            for variant in parsed_sv_variants)

#############################################################
##################### File fixtures #####################
#############################################################

@pytest.fixture
def config_file(request):
    """Get the path to a config file"""
    print('')
    return scout_yaml_config

@pytest.fixture
def panel_1_file(request):
    """Get the path to a config file"""
    print('')
    return panel_1_path

@pytest.fixture
def hgnc_file(request):
    """Get the path to a hgnc file"""
    print('')
    return hgnc_path

@pytest.fixture
def transcripts_file(request):
    """Get the path to a ensembl transcripts file"""
    print('')
    return ensembl_transcript_path

@pytest.fixture
def exac_file(request):
    """Get the path to a exac genes file"""
    print('')
    return exac_genes_path

@pytest.fixture
def hpo_genes_file(request):
    """Get the path to the hpo genes file"""
    print('')
    return hpo_genes_path

@pytest.fixture
def hpo_terms_file(request):
    """Get the path to the hpo terms file"""
    print('')
    return hpo_terms_path

@pytest.fixture
def hpo_disease_file(request):
    """Get the path to the hpo disease file"""
    print('')
    return hpo_disease_path

@pytest.fixture
def mim2gene_file(request):
    """Get the path to the mim2genes file"""
    print('')
    return mim2gene_path

@pytest.fixture
def mimtitles_file(request):
    """Get the path to the mim2genes file"""
    print('')
    return mimtitles_path

@pytest.fixture
def genemap_file(request):
    """Get the path to the mim2genes file"""
    print('')
    return genemap_path

@pytest.fixture(scope='function')
def variant_clinical_file(request):
    """Get the path to a variant file"""
    print('')
    return vcf_clinical_file

@pytest.fixture(scope='function')
def sv_clinical_file(request):
    """Get the path to a variant file"""
    print('')
    return sv_clinical_path


@pytest.fixture(scope='function')
def ped_file(request):
    """Get the path to a ped file"""
    print('')
    return ped_path


@pytest.fixture(scope='function')
def scout_config(request, config_file):
    """Return a dictionary with scout configs"""
    print('')
    in_handle = get_file_handle(config_file)
    data = yaml.load(in_handle)
    return data

@pytest.fixture(scope='function')
def minimal_config(request, scout_config):
    """Return a minimal config"""
    config = scout_config
    config.pop('madeline')
    config.pop('vcf_sv')
    config.pop('vcf_snv_research')
    config.pop('vcf_sv_research')
    config.pop('gene_panels')
    config.pop('default_gene_panels')
    config.pop('rank_model_version')
    config.pop('rank_score_threshold')
    config.pop('human_genome_build')

    return config

@pytest.fixture
def hgnc_handle(request, hgnc_file):
    """Get a file handle to a hgnc file"""
    print('')
    return get_file_handle(hgnc_file)

@pytest.fixture
def hgnc_genes(request, hgnc_handle):
    """Get a dictionary with hgnc genes"""
    print('')
    return parse_hgnc_genes(hgnc_handle)

@pytest.fixture
def transcripts_handle(request, transcripts_file):
    """Get a file handle to a ensembl transcripts file"""
    print('')
    return get_file_handle(transcripts_file)

@pytest.fixture
def transcripts(request, transcripts_handle):
    """Get the parsed ensembl transcripts"""
    print('')
    return parse_ensembl_transcripts(transcripts_handle)

@pytest.fixture
def exac_handle(request, exac_file):
    """Get a file handle to a ensembl gene file"""
    print('')
    return get_file_handle(exac_file)

@pytest.fixture
def exac_genes(request, exac_handle):
    """Get the parsed exac genes"""
    print('')
    return parse_exac_genes(exac_handle)

@pytest.fixture
def hpo_genes_handle(request, hpo_genes_file):
    """Get a file handle to a hpo gene file"""
    print('')
    return get_file_handle(hpo_genes_file)

@pytest.fixture
def mim2gene_handle(request, mim2gene_file):
    """Get a file handle to a mim2genes file"""
    print('')
    return get_file_handle(mim2gene_path)

@pytest.fixture
def mimtitles_handle(request, mimtitles_file):
    """Get a file handle to a mim2genes file"""
    print('')
    return get_file_handle(mimtitles_file)

@pytest.fixture
def genemap_handle(request, genemap_file):
    """Get a file handle to a mim2genes file"""
    print('')
    return get_file_handle(genemap_file)


@pytest.fixture
def hpo_genes(request, hpo_genes_handle):
    """Get the exac genes"""
    print('')
    return parse_hpo_genes(hpo_genes_handle)
