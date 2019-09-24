#-*- coding: utf-8 -*-
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import MissingError, AccessError, ValidationError
from odoo import api, fields, models, _
import os
import csv
import getpass
import codecs
from datetime import datetime
from dateutil import relativedelta


import logging
_logger = logging.getLogger(__name__)

statment_header = "IdTiers;TypeRelevé;TypeCompteur;NuméroSérie;NumContrat;NuméroFacture;NuméroRelevé;DateRelevé;DateDébutPériode;DateFinPériode;CompteurRelevé;Consommation;VolumeDépassement"
counter_header = "CleCollectePP;CodeConcession;NomConcession;Adresse1Concession;Adress2Concession;CodePostalConcession;VilleConcession;EmailConcession;TéléphoneConcession;FaxConcession;CodeClient;NomClient;CiviliteContact;NomContact;PrénomContact;EmailContact;FaxContact;MotDePasse;LibelléContrat;NuméroSérie;Localisation;DateLimite;CodeCompteur1;CodeCompteur2;CodeCompteur3;CodeCompteur4;DernierCompteur1;DernierCompteur2;DernierCompteur3;DernierCompteur4;URL"
contract_header = "Domaine;TypeContrat;IdTiers;IdContrat;NumContrat;NuméroSérie;RéférenceProduit;Forfait;PageSupNoir;PageSupCoul;CopiesInclusesNoir;CopiesInclusesCoul;CompteurDépartNoir;CompteurDépartCoul;DateDébutContrat;DateFinContrat;Actif;Terme;CodeClientPayeur;FréquenceFacturation;ConditionRèglement;DateCalage;DateAnniversaire;RéférenceCommande;ProchainePériodeFacturéeDébut;ProchainePériodeFacturéeFin;PageSupCpt3;CopiesInclusesCpt3;CompteurDépartCpt3;CodeClientLivré;PageSupCpt4;CopiesInclusesCpt4;CompteurDépartCpt4;DateResilation;CopiesEstimeesNB;CopiesEstimeesCoul;CopiesEstimeesCpt3;CopiesEstimeesCpt4;Engagement;Statut;Catégorie;Nature;DateCalageReleve;ContactCivilite;ContactNom;ContactPrenom;ContactEMail;ForfaitTotal;PageSupNoirTotal;PageSupCoulTotal;PageSupCpt3Total;PageSupCpt4Total;XPPS;Commercial"
invoice_line_header = "Domaine;IdLigne;IdFacture;IdTiers;NumFacture;Facture-Avoir;DateFacture;IdContrat;NumContrat;AnnéeContrat;NuméroSérie;RéfArticle;TypeArticle;Désignation;PxUnitaire;Remise;PxUnitaireNet;Qté;TotalHT;IdTiersContrat;CompteTiersContrat;CompteTiersFacturé;DatePeriodeDebut;DatePeriodeFin"
invoice_header = "Domaine;IdTiers;AnnéeContrat;Facture-Avoir;TypeFacture;NumFacture;DateFacture;DateEchéance;ConditionRèglement;TotalHT;TotalTVA;TotalTTC;NumRelevé;DateRelevé;DateDébutPériode;DateFinPériode;CompteurNoir;CompteurCoul;ConsommationNoir;ConsommationCoul;VolumeDépassementNoir;VolumeDépassementCoul;MontantForfaitFacturé;MontantDépassementNoirFacturé;MontantDépassementCoulFacturé;NumContrat;IdTiersContrat;CompteTiersContrat;CompteTiersFacturé"
picking_line_header = "Domaine;IdLigne;IdPièce;IdTiers;NumPièce;TypePièce;DatePièce;IdContrat;NumContrat;AnnéeContrat;NuméroSérie;RéfArticle;TypeArticle;Désignation;PxUnitaire;Remise;PxUnitaireNet;Qté;TotalHT;IdTiersContrat;CompteTiersContrat;CompteTiersFacturé;DatePeriodeDebut;DatePeriodeFin"



class FileLoader(models.TransientModel):
    """
    TransientModel utility object to load file and extract the needed data daily 
    """
    _name = 'file.loader'
    _description = 'Utility to load files from mounted disk'


    def __init__(self, pool, cr):
        """
            since we are using a TransientModel from a cron object
            the TransientModel is not created yet in the database (there's no call to create method on this model)
            we add the fields as pure python object not an Odoo Model
        """
        models.TransientModel.__init__(self, pool, cr)
        self.statement_file_path = False
        self.counter_file_path = False
        self.contract_file_path = False
        self.invoice_line_file_path = False
        self.invoice_file_path = False
        self.picking_line_path = False


        self.statement_header = statment_header.split(';')
        self.counter_header = counter_header.split(';')
        self.contract_header = contract_header.split(';')
        self.invoice_line_header = invoice_line_header.split(';')
        self.invoice_header = invoice_header.split(';')
        self.picking_line_header = picking_line_header.split(';')

        self.statement_data = False
        self.counter_data = False
        self.contract_data = False
        self.invoice_line_data = False
        self.invoice_data = False
        self.picking_line_data = False

    def sanitize_row(self, row):
        # remove any space, tab, newline, ...
        return ''.join(row.split())


    def load_files(self):
        self.validate_files()

        self.validate_statement_header()
        self.validate_counter_header()
        self.validate_contract_header()
        self.validate_picking_line_header()

        self.validate_invoice_line_header()
        self.validate_invoice_header()

        self.validate_machine()

        self.update_record()


    def read_file(self,absolute_path):
        data = None
        try:
            with codecs.open(absolute_path, encoding ='ISO-8859-1') as f:
                data = f.readlines()
        except Exception:
            raise AccessError('Could not read file: %s'%absolute_path)
        return data

    '''-----------------------------------------------validate file existans--------------------------------------------------'''
    @api.model
    def validate_files(self):

        mounted_path = self.env['ir.config_parameter'].sudo().get_param('passerelle.mounted_path', False)
        statement_file_name = self.env['ir.config_parameter'].sudo().get_param('passerelle.statement_file_name', False)
        counter_file_name = self.env['ir.config_parameter'].sudo().get_param('passerelle.counter_file_name', False)
        contract_file_name = self.env['ir.config_parameter'].sudo().get_param('passerelle.contract_file_name', False)
        invoice_line_file_name = self.env['ir.config_parameter'].sudo().get_param('passerelle.invoice_line_file_name', False)
        invoice_file_name = self.env['ir.config_parameter'].sudo().get_param('passerelle.invoice_file_name', False)
        picking_line_file_name = self.env['ir.config_parameter'].sudo().get_param('passerelle.picking_line_file_name', False)
        # check if all configuration attributes are set 
        if not statement_file_name:
            raise MissingError("Missing statement file name in the configuration !")
        if not counter_file_name:
            raise MissingError("Missing counter file name in the configuration !")
        if not contract_file_name:
            raise MissingError("Missing contract file name in the configuration !")
        if not invoice_line_file_name:
            raise MissingError("Missing invoice line file name in the configuration !")
        if not invoice_file_name:
            raise MissingError("Missing invoice file name in the configuration !")
        if not picking_line_file_name:
            raise MissingError("Missing picking line file name in the configuration !")
        if not mounted_path:
            raise MissingError("Missing mounted path in the configuration !")

        # validate that the mounted path exist and it's a directory
        if not os.path.isdir(mounted_path):
            raise ValidationError('The specified path cannot be located on this system')

        files_names = [statement_file_name, counter_file_name, contract_file_name, invoice_line_file_name, invoice_file_name,picking_line_file_name]

        # validate that all files exists and current user (user running the script odoo user) have read permission on them 
        for file_name in files_names:
            absolute_path = mounted_path+'/'+file_name
            # check if file exists and the path points to a file
            if not os.path.exists(absolute_path) or not os.path.isfile(absolute_path):
                raise MissingError("%s is not a file or the specified file doesn't exist"%file_name)
            # check if current user (odoo user) have read permission on the current file
            if not os.access(absolute_path, os.R_OK):
                raise AccessError("User %s don't have read permission on the specified directory"%getpass.getuser())   
        # set the values on pure python object attributes
        self.statement_file_path = mounted_path+'/'+statement_file_name
        self.counter_file_path = mounted_path+'/'+counter_file_name
        self.contract_file_path = mounted_path+'/'+contract_file_name
        self.invoice_line_file_path = mounted_path+'/'+invoice_line_file_name
        self.invoice_file_path = mounted_path+'/'+invoice_file_name
        self.picking_line_file_path = mounted_path+'/'+picking_line_file_name

        self.statement_header = statment_header.split(';')
        self.counter_header = counter_header.split(';')
        self.contract_header = contract_header.split(';')
        self.invoice_line_header = invoice_line_header.split(';')
        self.invoice_header = invoice_header.split(';')
        self.picking_line_header = picking_line_header.split(';')

        self.statement_data = False
        self.counter_data = False
        self.contract_data = False
        self.invoice_line_data = False
        self.invoice_data = False
        self.picking_line_data = False
        return True

    '''-----------------------------------------------Validate files header--------------------------------------------------'''
    
    def validate_machine(self):
        # get the index of serialNumber attribute from static header
        machine_serial_number_index = self.statement_header.index('NuméroSérie')
        unique_serial_number_list = self.get_unique_list_of_machines_serial_numbers(machine_serial_number_index, self.statement_data)

        record_id = self.env['file.machine'].search([])
        if record_id:
            record_id.unlink()

        for rec in unique_serial_number_list:
            vals = {
                'NumeroSerie'  : rec,
            }
            self.env['file.machine'].create(vals)


    def validate_statement_header(self):
        # extract the data lines from the specified absolute path
        data = self.read_file(self.statement_file_path)
        # read the header attributes 
        file_header = self.sanitize_row(data[0]).split(';')
        # validate header attributes
        for key in self.statement_header:
            if key not in file_header:
                raise MissingError("Missing attribute statement_header %s"%key)
        # remove the header
        data.pop(0)
        # store the data in object attribute
        self.statement_data = [self.sanitize_row(row).split(';') for row in data]
        record_id = self.env['file.releve'].search([])
        if record_id:
            record_id.unlink()
        for rec in self.statement_data:
            vals = {
                'TypeReleve'  : rec[1],
                'TypeCompteur'    : rec[2],
                'NumeroSerie'     : rec[3],
                'NumContrat'  : rec[4],
                'NumeroFacture'   : rec[5],
                'NumeroReleve'    : rec[6],
                'DateReleve'  : rec[7],
                'DateDebutPeriode'    : rec[8],
                'DateFinPeriode'  : rec[9],
                'CompteurReleve'  : rec[10],
                'Consommation'    : rec[11],
                'VolumeDepassement'   : rec[12],
            }
            
            self.env['file.releve'].create(vals)


    def validate_counter_header(self):
        # extract the data lines from the specified absolute path
        data = self.read_file(self.counter_file_path)
        # read the header attributes 
        file_header = self.sanitize_row(data[0]).split(';')
        # validate header attributes
        for key in self.counter_header:
            if key not in file_header:
                raise MissingError("Missing attribute counter_header %s"%key)
        # remove the header
        data.pop(0)
        # store the data in object attribute
        self.counter_data = [self.sanitize_row(row).split(';') for row in data]
        record_id = self.env['file.compteur'].search([])
        if record_id:
            record_id.unlink()
        
        for rec in self.counter_data:
            vals = {
                'CodeConcession'  : rec[self.counter_header.index('CodeConcession')],
                'NomConcession'    : rec[self.counter_header.index('NomConcession')],
                'CodeClient'     : rec[self.counter_header.index('CodeClient')],
                'NumeroSerie'  : rec[self.counter_header.index('NuméroSérie')],
                'DateLimite'   : rec[self.counter_header.index('DateLimite')],
                'CodeCompteur1'    : rec[self.counter_header.index('CodeCompteur1')],
                'CodeCompteur2'  : rec[self.counter_header.index('CodeCompteur2')],
                'DernierCompteur1'  : rec[self.counter_header.index('DernierCompteur1')],
                'DernierCompteur2'    : rec[self.counter_header.index('DernierCompteur2')],
                
            }
            self.env['file.compteur'].create(vals)
            

    def validate_contract_header(self):
        # extract the data lines from the specified absolute path
        data = self.read_file(self.contract_file_path)
        # read the header attributes 
        file_header = self.sanitize_row(data[0]).split(';')
        # validate header attributes
        for key in self.contract_header:
            if key not in file_header:
                raise MissingError("Missing attribute contract_header %s"%key)
        # remove the header
        data.pop(0)
        # store the data in object attribute
        self.contract_data = [self.sanitize_row(row).split(';') for row in data]
        record_id = self.env['file.contrat'].search([])
        if record_id:
            record_id.unlink()
        for rec in self.contract_data:
            vals = {
                'Domaine'  : rec[self.contract_header.index('Domaine')],
                'TypeContrat'    : rec[self.contract_header.index('TypeContrat')],
                'IdTiers'     : rec[self.contract_header.index('IdTiers')],
                'IdContrat'  : rec[self.contract_header.index('IdContrat')],
                'NumContrat'   : rec[self.contract_header.index('NumContrat')],
                'NumeroSerie'    : rec[self.contract_header.index('NuméroSérie')],
                'ReferenceProduit'  : rec[self.contract_header.index('RéférenceProduit')],
                'Forfait'  : rec[self.contract_header.index('Forfait')],
                
                'PageSupNoir'  : rec[self.contract_header.index('PageSupNoir')],
                'PageSupCoul'    : rec[self.contract_header.index('PageSupCoul')],
                'CompteurDepartNoir'    : rec[self.contract_header.index('CompteurDépartNoir')],
                'CompteurDepartCoul'    : rec[self.contract_header.index('CompteurDépartCoul')],
                'CopiesInclusesNoir'    : rec[self.contract_header.index('CopiesInclusesNoir')],
                'DateDebutContrat'    : rec[self.contract_header.index('DateDébutContrat')],
                'DateFinContrat'    : rec[self.contract_header.index('DateFinContrat')],
                'Engagement'    : rec[self.contract_header.index('Engagement')],
            }
            self.env['file.contrat'].create(vals)



    def validate_invoice_line_header(self):
        # extract the data lines from the specified absolute path
        # print "##### FILE NAME ",self.invoice_line_file_path
        data = self.read_file(self.invoice_line_file_path)
        # read the header attributes 
        file_header = self.sanitize_row(data[0]).split(';')
        # validate header attributes
        for key in self.invoice_line_header:
            # print("key ",key)
            # print("### HEADER ",file_header)
            if key not in file_header:
                raise MissingError("Missing attribute invoice_line_header %s"%key)
        # remove the header
        data.pop(0)
        # store the data in object attribute
        self.invoice_line_data = [self.sanitize_row(row).split(';') for row in data]
        record_id = self.env['file.ligne.facture'].search([])
        if record_id:
            record_id.unlink()
        for rec in self.invoice_line_data:
            vals = {
                'Domaine'  : rec[self.invoice_line_header.index('Domaine')],
                'IdLigne'    : rec[self.invoice_line_header.index('IdLigne')],
                'IdFacture'     : rec[self.invoice_line_header.index('IdFacture')],
                'IdTiers'  : rec[self.invoice_line_header.index('IdTiers')],
                'Facture_Avoir'   : rec[self.invoice_line_header.index('Facture-Avoir')],
                'DateFacture'    : rec[self.invoice_line_header.index('DateFacture')],
                'IdContrat'  : rec[self.invoice_line_header.index('IdContrat')],
                'NumContrat'  : rec[self.invoice_line_header.index('NumContrat')],
                
                'AnneeContrat'  : rec[self.invoice_line_header.index('AnnéeContrat')],
                'NumeroSerie'    : rec[self.invoice_line_header.index('NuméroSérie')],
                'RefArticle'    : rec[self.invoice_line_header.index('RéfArticle')],
                'TypeArticle'    : rec[self.invoice_line_header.index('TypeArticle')],
                'Designation'    : rec[self.invoice_line_header.index('Désignation')],
                'PxUnitaire'    : rec[self.invoice_line_header.index('PxUnitaire')],
                'Remise'    : rec[self.invoice_line_header.index('Remise')],
                'PxUnitaireNet'    : rec[self.invoice_line_header.index('PxUnitaireNet')],

                'Qte'  : rec[self.invoice_line_header.index('Qté')],
                'TotalHT'    : rec[self.invoice_line_header.index('TotalHT')],
                'IdTiersContrat'    : rec[self.invoice_line_header.index('IdTiersContrat')],
                'CompteTiersContrat'    : rec[self.invoice_line_header.index('CompteTiersContrat')],
                'CompteTiersFacture'    : rec[self.invoice_line_header.index('CompteTiersFacturé')],
                'DatePeriodeDebut'    : rec[self.invoice_line_header.index('DatePeriodeDebut')],
                'DatePeriodeFin'    : rec[self.invoice_line_header.index('DatePeriodeFin')],
            }
            self.env['file.ligne.facture'].create(vals)

    def validate_invoice_header(self):
        # extract the data lines from the specified absolute path
        # print "##### FILE NAME ",self.invoice_file_path
        data = self.read_file(self.invoice_file_path)
        # read the header attributes 
        file_header = self.sanitize_row(data[0]).split(';')
        # validate header attributes
        for key in self.invoice_header:
            # print("key ",key)
            # print("### HEADER ",file_header)
            if key not in file_header:
                raise MissingError("Missing attribute invoice_header %s"%key)
        # remove the header
        data.pop(0)
        # store the data in object attribute
        self.invoice_data = [self.sanitize_row(row).split(';') for row in data]

    def validate_picking_line_header(self):
        # extract the data lines from the specified absolute path
        # print "##### FILE NAME ",self.invoice_file_path
        data = self.read_file(self.picking_line_file_path)
        print("###### picking_line_file_path ",self.picking_line_file_path)
        # read the header attributes 
        file_header = self.sanitize_row(data[0]).split(';')
        print("###### PCIKING ",file_header)
        print("###### PCIKING HEADER ",self.picking_line_header)
        
        # validate header attributes
        for key in self.picking_line_header:
            # print("key ",key)
            # print("### HEADER ",file_header)
            if key not in file_header:
                raise MissingError("Missing attribute picking_line_header %s"%key)
        # remove the header
        data.pop(0)
        # store the data in object attribute
        self.picking_line_data = [self.sanitize_row(row).split(';') for row in data]
        record_id = self.env['file.bl.ligne'].search([])
        if record_id:
            record_id.unlink()
        for rec in self.picking_line_data:
            vals = {
                'Domaine'  : rec[self.picking_line_header.index('Domaine')],
                'IdLigne'    : rec[self.picking_line_header.index('IdLigne')],
                'IdPiece'     : rec[self.picking_line_header.index('IdPièce')],
                'IdTiers'  : rec[self.picking_line_header.index('IdTiers')],
                'TypePiece'   : rec[self.picking_line_header.index('TypePièce')],
                'DatePiece'    : rec[self.picking_line_header.index('DatePièce')],
                'IdContrat'  : rec[self.picking_line_header.index('IdContrat')],
                'NumContrat'  : rec[self.picking_line_header.index('NumContrat')],
                
                'AnneeContrat'  : rec[self.picking_line_header.index('AnnéeContrat')],
                'NumeroSerie'    : rec[self.picking_line_header.index('NuméroSérie')],
                'RefArticle'    : rec[self.picking_line_header.index('RéfArticle')],
                'TypeArticle'    : rec[self.picking_line_header.index('TypeArticle')],
                'Designation'    : rec[self.picking_line_header.index('Désignation')],
                'PxUnitaire'    : rec[self.picking_line_header.index('PxUnitaire')],
                'Remise'    : rec[self.picking_line_header.index('Remise')],
                'PxUnitaireNet'    : rec[self.picking_line_header.index('PxUnitaireNet')],
                'Qte'    : rec[self.picking_line_header.index('Qté')],
                'TotalHT'    : rec[self.picking_line_header.index('TotalHT')],
                'DatePeriodeDebut'    : rec[self.picking_line_header.index('DatePeriodeDebut')],
                'DatePeriodeFin'    : rec[self.picking_line_header.index('DatePeriodeFin')],              
            }
            self.env['file.bl.ligne'].create(vals)
        

    def update_record(self):
        # get the index of serialNumber attribute from static header
        machine_serial_number_index = self.statement_header.index('NuméroSérie')
        counter_index = self.statement_header.index('CompteurRelevé')
        statement_id_index = self.statement_header.index('NuméroRelevé')
        counter_type_index = self.statement_header.index('TypeCompteur')
        contract_number_index = self.statement_header.index('NumContrat')
        

        unique_serial_number_list = self.get_unique_list_of_machines_serial_numbers(machine_serial_number_index, self.statement_data)
        for serial_number in unique_serial_number_list:
            # list of records either with two records NB and CO or one of them.
            lines = self.get_statement_of_machine(serial_number)
           
            if len(lines):
                NB_counter_value = 0
                CO_counter_value = 0
                row_1 = lines[0]
                row_2 = lines[1] if len(lines)>1 else False
                
                if row_1[counter_type_index] == 'NB':
                    NB_counter_value = int(row_1[counter_index])
                else:
                    CO_counter_value = int(row_1[counter_index])

                if row_2:
                    if row_2[counter_type_index] == 'CO':
                        CO_counter_value = int(row_2[counter_index])
                    else:
                        NB_counter_value = int(row_2[counter_index])

                contract_number = row_1[contract_number_index]
                # print "#### CONTRACT ",contract_number


                invoice_lines = self.get_invoice_lines(contract_number)
                
                product_type_index = self.invoice_line_header.index('TypeArticle')
                unit_price_index = self.invoice_line_header.index('PxUnitaireNet')
                
                total_ttc = 0
                last_statement_date = False
                NB_cost_value = 0
                CO_cost_value = 0
                if invoice_lines:
                    row_1 = invoice_lines[0]
                    row_2 = invoice_lines[1] if len(invoice_lines)>1 else False
                    if row_1[product_type_index] == 'CPTNB':
                        NB_cost_value = float(row_1[unit_price_index].replace(',','.'))
                    else:
                        CO_cost_value = float(row_1[unit_price_index].replace(',','.'))

                    if row_2:
                        if row_2[product_type_index] == 'CPTCO':
                            CO_cost_value = float(row_2[unit_price_index].replace(',','.'))
                        else:
                            NB_cost_value = float(row_2[unit_price_index].replace(',','.'))

                    invoice_index = self.invoice_line_header.index('NumFacture')
                    total_ttc_index = self.invoice_header.index('TotalTTC')
                    last_statement_date_index = self.invoice_header.index('DateRelevé')

                    # at least there's one invoice line. using the NumFacture attribute of the first record to get the invoice record
                    invoice = self.get_invoice(invoice_lines[0][invoice_index])
                    total_ttc = invoice[total_ttc_index]
                    last_statement_date = invoice[last_statement_date_index]
                    last_statement_date = datetime.strptime(last_statement_date, '%d/%m/%Y').date()
                    # print '------------ last_statement_date ',last_statement_date


                # vals = {
                #     'name':serial_number,
                #     'machine_serial_number':serial_number,
                #     'color_copies_number':CO_counter_value,
                #     'black_white_copies_number':NB_counter_value,
                #     'contract_number':contract_number,
                #     'cost_black_white_page':NB_cost_value,
                #     'cost_per_color_page':CO_cost_value
                # }

                machine_serial_number_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.machine_serial_number', False)
                black_white_counter_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.black_white_counter', False)
                color_counter_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.color_counter', False)
                contract_number_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.contract_number', False)
                black_white_cost_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.black_white_cost', False)
                color_cost_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.color_cost', False)
                total_ttc_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.total_ttc', False)
                last_statement_date_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.last_statement_date', False)
                last_auto_update_date_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.last_auto_update_date', False)
                contract_periode_field = self.env['ir.config_parameter'].sudo().get_param('passerelle.contract_periode', False)

                vals = {
                    # 'name':serial_number,
                    # N° Série Machine
                    machine_serial_number_field:serial_number,
                    # Engagement NB
                    color_counter_field:CO_counter_value,
                    # Engagement COUL
                    black_white_counter_field:NB_counter_value,
                    # N° Contrat
                    contract_number_field:contract_number,
                    # Coût Page NB
                    black_white_cost_field:NB_cost_value,
                    # Coût page COUL
                    color_cost_field:CO_cost_value,
                    # Engagement Total facture
                    total_ttc_field:total_ttc,

                    # Date dernier relevé 
                    last_statement_date_field:last_statement_date,

                    # Date dernier mise à jour automatique
                    last_auto_update_date_field:fields.Datetime.now()
                }
                
                contract_line = self.get_contract(contract_number)
                if contract_line:
                    start_date_index = self.contract_header.index('DateDébutContrat')
                    end_date_index = self.contract_header.index('DateFinContrat')

                    start_date = datetime.strptime(contract_line[start_date_index], '%d/%m/%Y').date()
                    end_date = datetime.strptime(contract_line[end_date_index], '%d/%m/%Y').date()

                    delta = relativedelta.relativedelta(end_date, start_date)
                    months = delta.years * 12 + delta.months
                    vals[contract_periode_field] = months
                
                rec = self.env['x_parc'].search([('x_studio_field_Y3N9k','=',serial_number)])
                if rec:
                    rec.write(vals)                        
                else:
                    self.env['x_parc'].create(vals)
                
    def get_contract(self, contract_number):
        domaine_index = self.contract_header.index('Domaine') # can be V or A => Vente/ Achat
        contract_number_index = self.contract_header.index('NumContrat')
        for line in self.contract_data:
            if line[domaine_index] == 'V' and line[contract_number_index] == contract_number:
                return line

    def get_invoice(self, invoice_number):
        """ 
            each invoice has one unique number
        """
        invoice_number_index = self.invoice_header.index('NumFacture')
        for line in self.invoice_data:
            if line[invoice_number_index] == invoice_number:
                return line
        return False


    def get_invoice_lines(self, contract_number):
        # V;1400169;130302;3613;FCP40963;F;06/02/2019;2472;3402546189;2016;3188488527;CPPNB;CPTNB;COPIES SUPPLEMENTAIRES NOIR & BLANC;
        # 0,010650;0,0000000000;0,010650;218,000000;2,320000;3613;1MEDIA;1MEDIA;01/11/2018;31/01/2019

        # V;1400173;130302;3613;FCP40963;F;06/02/2019;2472;3402546189;2016;3188488527;CPPC;CPTCO;COPIES SUPPLEMENTAIRES COULEUR;
        # 0,129580;0,0000000000;0,129580;687,000000;89,020000;3613;1MEDIA;1MEDIA;01/11/2018;31/01/2019

        # V;1400176;130302;3613;FCP40963;F;06/02/2019;2472;3402546189;2016;3188488527;FRAIS;FORFAIT;FRAIS DE RECYCLAGE;
        # 3,000000;0,0000000000;3,000000;1,000000;3,000000;3613;1MEDIA;1MEDIA;01/11/2018;31/01/2019

        domaine_index = self.invoice_line_header.index('Domaine') # can be V or A => Vente/ Achat
        contract_number_index = self.invoice_line_header.index('NumContrat')
        product_type_index = self.invoice_line_header.index('TypeArticle')
        invoice_lines = []
        for line in self.invoice_line_data:
            if line[domaine_index] == 'V' and line[contract_number_index] == contract_number and line[product_type_index] in ['CPTNB','CPTCO']:
                invoice_lines.append(line)
        invoice_lines = self.get_last_invoice_line(invoice_lines)
        return invoice_lines

    def get_last_invoice_line(self, invoice_lines):
        ''' Exemple of date to process'''
        # 3235;Réel;NB;3327190910;3402143965M;;110455;31/01/2019;01/01/2019;31/01/2019;15486;160;160
        # 3235;Réel;NB;3327190910;3402143965M;;108820;31/12/2018;01/12/2018;31/12/2018;15326;135;135

        # 3235;Réel;CO;3327190910;3402143965M;;110456;31/01/2019;01/01/2019;31/01/2019;10891;997;997
        # 3235;Réel;CO;3327190910;3402143965M;;108821;31/12/2018;01/12/2018;31/12/2018;9894;946;946


        NB_line = False
        CO_line = False
        result = []
        product_type_index = self.invoice_line_header.index('TypeArticle')
        invoice_date_index = self.invoice_line_header.index('DateFacture')
        for rec in invoice_lines:
            if rec[product_type_index] == 'CPTNB':
                # get the most recent line with NB (noir et blanc) couter type
                # if it's the first iteration store the line
                if NB_line == False:
                    NB_line = rec
                else:
                    # compare date and keep the recent element only
                    current_date = datetime.strptime(rec[invoice_date_index], '%d/%m/%Y').date()
                    last_date = datetime.strptime(NB_line[invoice_date_index], '%d/%m/%Y').date()
                    if current_date > last_date:
                        NB_line = rec
            elif rec[product_type_index] == 'CPTCO':
                # get the most recent line with CO (couleur) couter type
                # if it's the first iteration store the line
                if CO_line == False:
                    CO_line = rec
                else:
                    # compare date and keep the recent element only
                    current_date = datetime.strptime(rec[invoice_date_index], '%d/%m/%Y').date()
                    last_date = datetime.strptime(CO_line[invoice_date_index], '%d/%m/%Y').date()
                    if current_date > last_date:
                        CO_line = rec

        if NB_line:
            result.append(NB_line)
        if CO_line:
            result.append(CO_line)
        return result





    def get_unique_list_of_machines_serial_numbers(self, serial_number_index, data_list):
        """
            a file can contain a serial number for the same machine in multiple lines
        """
        # iterate through the data list and get the serial number from each line using it's index
        # remove duplication from the generated list using dict.fromkeys()
        return list(dict.fromkeys([line[serial_number_index] for line in data_list]))
        

    def get_statement_of_machine(self, machine_serial_number):
        ''' 
            at most return list with two element for a SINGLE MACHINE
            one for the NB if exists and the second element for CO if exists 
        '''
        statement_lines = []
        machine_serial_number_index = self.statement_header.index('NuméroSérie')
        statement_id_index = self.statement_header.index('NuméroRelevé')
        counter_type_index = self.statement_header.index('TypeCompteur')
        for line in self.statement_data:
            if line[machine_serial_number_index] == machine_serial_number and line[counter_type_index] in ['NB','CO']:
                statement_lines.append(line)
        # print "######### LEN OF DATA ",len(statement_lines)
        statement_lines = self.get_last_statement_for_counter_type(statement_lines)
        return statement_lines



    def get_last_statement_for_counter_type(self, statement_lines):
        ''' Exemple of date to process'''
        # 3235;Réel;NB;3327190910;3402143965M;;110455;31/01/2019;01/01/2019;31/01/2019;15486;160;160
        # 3235;Réel;NB;3327190910;3402143965M;;108820;31/12/2018;01/12/2018;31/12/2018;15326;135;135

        # 3235;Réel;CO;3327190910;3402143965M;;110456;31/01/2019;01/01/2019;31/01/2019;10891;997;997
        # 3235;Réel;CO;3327190910;3402143965M;;108821;31/12/2018;01/12/2018;31/12/2018;9894;946;946


        NB_line = False
        CO_line = False
        result = []
        statement_date_index = self.statement_header.index('DateRelevé')
        counter_type_index = self.statement_header.index('TypeCompteur')
        for rec in statement_lines:
            if rec[counter_type_index] == 'NB':
                # get the most recent line with NB (noir et blanc) couter type
                # if it's the first iteration store the line
                if NB_line == False:
                    NB_line = rec
                else:
                    # compare date and keep the recent element only
                    current_date = datetime.strptime(rec[statement_date_index], '%d/%m/%Y').date()
                    last_date = datetime.strptime(NB_line[statement_date_index], '%d/%m/%Y').date()
                    if current_date > last_date:
                        NB_line = rec
            elif rec[counter_type_index] == 'CO':
                # get the most recent line with CO (couleur) couter type
                # if it's the first iteration store the line
                if CO_line == False:
                    CO_line = rec
                else:
                    # compare date and keep the recent element only
                    current_date = datetime.strptime(rec[statement_date_index], '%d/%m/%Y').date()
                    last_date = datetime.strptime(CO_line[statement_date_index], '%d/%m/%Y').date()
                    if current_date > last_date:
                        CO_line = rec

        if NB_line:
            result.append(NB_line)
        if CO_line:
            result.append(CO_line)
        return result






    def validate_header(self, data):
        key_number = 0
        
        static_header = csv_header.split(';')
        serial_number_index = static_header.index('NuméroSérie')
        if not len(data):
            raise MissingError("File is empty")
        
        file_header = self.sanitize_row(data[0]).split(';')
        key_number = len(file_header)
        # 1- validate the header keys
        for key in static_header:
            if key not in file_header:
                raise MissingError("Missing attribute validate_header %s"%key)
        # 2- validate each row values (must be equal to the header keys number)
        # remove the header 
        data.pop(0)
        for row in data:
            row_list = self.sanitize_row(row).split(';')
            if len(row_list) != key_number:
                raise ValidationError('DATA ROW NUMBER IS INCORRECT')
            # print "########### ",self.sanitize_row(row).split(';')
            machine_serial_number = row_list[serial_number_index]
            self.env['x_parc'].create({'x_studio_field_Y3N9k':machine_serial_number})


    







"""                                             Facture
Domaine;
IdLigne;
IdFacture;                      <--------- Join attribute
IdTiers;
NumFacture;
Facture-Avoir;
DateFacture;
IdContrat;                      <--------- Join with contract
NumContrat;
AnnéeContrat;
NuméroSérie;
RéfArticle;
TypeArticle;
Désignation;
PxUnitaire;
Remise;
PxUnitaireNet;
Qté;
TotalHT;
IdTiersContrat;
CompteTiersContrat;
CompteTiersFacturé;
DatePeriodeDebut;
DatePeriodeFin
"""

# V;1400169;130302;3613;FCP40963;F;06/02/2019;2472;3402546189;2016;3188488527;CPPNB;CPTNB;COPIES SUPPLEMENTAIRES NOIR & BLANC;
# 0,010650;0,0000000000;0,010650;218,000000;2,320000;3613;1MEDIA;1MEDIA;01/11/2018;31/01/2019

# V;1400173;130302;3613;FCP40963;F;06/02/2019;2472;3402546189;2016;3188488527;CPPC;CPTCO;COPIES SUPPLEMENTAIRES COULEUR;
# 0,129580;0,0000000000;0,129580;687,000000;89,020000;3613;1MEDIA;1MEDIA;01/11/2018;31/01/2019

# V;1400176;130302;3613;FCP40963;F;06/02/2019;2472;3402546189;2016;3188488527;FRAIS;FORFAIT;FRAIS DE RECYCLAGE;
# 3,000000;0,0000000000;3,000000;1,000000;3,000000;3613;1MEDIA;1MEDIA;01/11/2018;31/01/2019



"""                                             Facture Ligne
Domaine;
IdLigne;
IdFacture;
IdTiers;
NumFacture;
Facture-Avoir;
DateFacture;
IdContrat;
NumContrat;
AnnéeContrat;
NuméroSérie;
RéfArticle;
TypeArticle;
Désignation;
PxUnitaire;
Remise;
PxUnitaireNet;
Qté;
TotalHT;
IdTiersContrat;
CompteTiersContrat;
CompteTiersFacturé;
DatePeriodeDebut;
DatePeriodeFin
"""

"""                                             Compteurs
CleCollectePP;
CodeConcession;
NomConcession;
Adresse1Concession;
Adress2Concession;
CodePostalConcession;
VilleConcession;
EmailConcession;
TéléphoneConcession;
FaxConcession;
CodeClient;
NomClient;
CiviliteContact;
NomContact;
PrénomContact;
EmailContact;
FaxContact;
MotDePasse;
LibelléContrat;
NuméroSérie;
Localisation;
DateLimite;
CodeCompteur1;
CodeCompteur2;
CodeCompteur3;
CodeCompteur4;
DernierCompteur1;
DernierCompteur2;
DernierCompteur3;
DernierCompteur4;
URL
"""


"""                                                 Releve
IdTiers;
TypeRelevé;
TypeCompteur;                   <---------- Couleur / Noir et blanc
NuméroSérie;                    <---------- Numéro de série machine
NumContrat;                     <---------- Numéro Contrat
NuméroFacture;                  <---------- peut contenir les cout par page
NuméroRelevé;                   <---------- jointure avec le fichier relevé
DateRelevé;                     <---------- date (comparaison pour savoir quel ligne à charger)
DateDébutPériode;
DateFinPériode;
CompteurRelevé;                 <---------- may be useful
Consommation;                   <---------- may be useful
VolumeDépassement
"""


# 3235;Réel;NB;3327190910;3402143965M;;110455;31/01/2019;01/01/2019;31/01/2019;15486;160;160
# 3235;Réel;NB;3327190910;3402143965M;;108820;31/12/2018;01/12/2018;31/12/2018;15326;135;135

# 3235;Réel;CO;3327190910;3402143965M;;110456;31/01/2019;01/01/2019;31/01/2019;10891;997;997
# 3235;Réel;CO;3327190910;3402143965M;;108821;31/12/2018;01/12/2018;31/12/2018;9894;946;946



# 3581;Réel;C3;AT1237966;3402312486;;109610;31/12/2018;01/10/2018;31/12/2018;1394;0;0
# 3581;Réel;C3;AT1237966;3402312486;;109611;31/12/2018;01/10/2018;31/12/2018;12241;2;2
# 3581;Réel;C3;AT1237966;3402312486;;109612;31/12/2018;01/10/2018;31/12/2018;12311;2;2

# 3483;Réel;NB;XFN196466;3402192737;;109678;31/01/2019;01/11/2018;31/01/2019;21690;1850;1850
# 3483;Réel;CO;XFN196466;3402192737;;109679;31/01/2019;01/11/2018;31/01/2019;29238;1841;1841


# V;Réel;3244;2817;3402797732;3354992743;C400V_DNM;0.000000;0.006870;0.068700;0;0;0;0;28/04/2017;30/06/2020;O;
# Echoir;1GVTDTAS;Trimestrielle;VIREMENT 45 jours nets;01/07/2017;;;28/04/2017;30/06/2017;0.000000;0;0;1GVTDTAS;0.000000;0;0;
# ;0,0000;0,0000;0,0000;0,0000;Trimestrielle;ACTIF;GVTREEL;SCI;30/06/2017;;;;;;0.00;0.00;0.00;0.00;;


# A;Réel;3244;2817;3402797732;3354992743;C400V_DNM;21.000000;0.004500;0.045000;0;0;0;0;28/04/2017;30/06/2020;O;
# Echoir;1GVTDTAS;Trimestrielle;VIREMENT 45 jours nets;01/07/2017;;;28/04/2017;30/06/2017;0.000000;0;0;1GVTDTAS;0.000000;0;0;
# ;0,0000;0,0000;0,0000;0,0000;Trimestrielle;ACTIF;GVTREEL;SCI;30/06/2017;;;;;;0.00;0.00;0.00;0.00;;

"""                                                 Contrat
Domaine;                    <------ Majuscules (1) ‘A’ / ‘V’ – Vente ou Achat
TypeContrat;                <------ Libre (11) : ‘Réel’ ou ‘Estimé’
IdTiers;
IdContrat;
NumContrat;
NuméroSérie;
RéférenceProduit;
Forfait;
PageSupNoir;
PageSupCoul;
CopiesInclusesNoir;
CopiesInclusesCoul;
CompteurDépartNoir;
CompteurDépartCoul;
DateDébutContrat;
DateFinContrat;
Actif;
Terme;
CodeClientPayeur;
FréquenceFacturation;
ConditionRèglement;
DateCalage;
DateAnniversaire;
RéférenceCommande;
ProchainePériodeFacturéeDébut;
ProchainePériodeFacturéeFin;
PageSupCpt3;
CopiesInclusesCpt3;
CompteurDépartCpt3;
CodeClientLivré;
PageSupCpt4;
CopiesInclusesCpt4;
CompteurDépartCpt4;
DateResilation;
CopiesEstimeesNB;
CopiesEstimeesCoul;
CopiesEstimeesCpt3;
CopiesEstimeesCpt4;
Engagement;
Statut;
Catégorie;
Nature;
DateCalageReleve;
ContactCivilite;
ContactNom;
ContactPrenom;
ContactEMail;
ForfaitTotal;
PageSupNoirTotal;
PageSupCoulTotal;
PageSupCpt3Total;
PageSupCpt4Total;
XPPS;
Commercial
"""
