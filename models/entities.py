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


class Contrat(models.Model):
    _name = 'file.contrat'

    Domaine             = fields.Char('Domain')
    TypeContrat = fields.Char('TypeContrat')
    IdTiers = fields.Char('IdTiers')
    IdContrat = fields.Char('IdContrat')
    NumContrat = fields.Char('NumContrat')
    NumeroSerie = fields.Char('NumeroSerie')
    ReferenceProduit = fields.Char('ReferenceProduit')
    Forfait = fields.Char('Forfait')
    PageSupNoir = fields.Char('PageSupNoir')
    PageSupCoul = fields.Char('PageSupCoul')
    CopiesInclusesNoir = fields.Char('CipieInclusesNoir')
    CompteurDepartNoir = fields.Char('CompteurDepartNoir')
    CompteurDepartCoul   = fields.Char('CompteurDepartCoul')
    DateDebutContrat = fields.Char('DateDebutContrat')
    DateFinContrat = fields.Char('DateFinContrat')
    Engagement = fields.Char('Engagement')


class Compteur(models.Model):
    _name = 'file.compteur'

    CodeConcession  = fields.Char('CodeConcession')
    NomConcession   = fields.Char('NomConcession')
    CodeClient  = fields.Char('CodeClient')
    NomClient   = fields.Char('NomClient')
    NumeroSerie = fields.Char('NumeroSerie')
    DateLimite  = fields.Char('DateLimite')
    CodeCompteur1   = fields.Char('CodeCompteur1')
    CodeCompteur2   = fields.Char('CodeCompteur2')
    DernierCompteur1    = fields.Char('DernierCompteur1')
    DernierCompteur2    = fields.Char('DernierCompteur2')
    

class Releve(models.Model):
    _name = 'file.releve'


    TypeReleve  = fields.Char('TypeReleve')
    TypeCompteur    = fields.Char('TypeCompteur')
    NumeroSerie     = fields.Char('NumeroSerie')
    NumContrat  = fields.Char('NumContrat')
    NumeroFacture   = fields.Char('NumeroFacture')
    NumeroReleve    = fields.Char('NumeroReleve')
    DateReleve  = fields.Char('DateReleve')
    DateDebutPeriode    = fields.Char('DateDebutPeriode')
    DateFinPeriode  = fields.Char('DateFinPeriode')
    CompteurReleve  = fields.Char('CompteurReleve')
    Consommation    = fields.Char('Consommation')
    VolumeDepassement   = fields.Char('VolumeDepassement')

class Facture(models.Model):
    _name = 'file.fatcure'


    Domaine     = fields.Char('Domaine')
    IdTiers = fields.Char('VolumeDepassement')
    AnneeContrat    = fields.Char('AnneeContrat')
    Facture_Avoir   = fields.Char('Facture_Avoir')
    TypeFacture = fields.Char('TypeFacture')
    NumFacture  = fields.Char('NumFacture')
    DateFacture = fields.Char('DateFacture')
    DateEcheance    = fields.Char('DateEcheance')
    TotalHT = fields.Char('TotalHT')
    TotalTVA    = fields.Char('TotalTVA')
    TotalTTC    = fields.Char('TotalTTC')
    NumReleve   = fields.Char('NumReleve')
    DateReleve  = fields.Char('DateReleve')
    DateDebutPeriode    = fields.Char('DateDebutPeriode')
    DateFinPeriode  = fields.Char('DateFinPeriode')
    CompteurNoir    = fields.Char('CompteurNoir')
    CompteurCoul    = fields.Char('CompteurCoul')
    ConsommationNoir    = fields.Char('ConsommationNoir')
    ConsommationCoul    = fields.Char('ConsommationCoul')
    VolumeDepassementNoir   = fields.Char('VolumeDepassementNoir')
    VolumeDepassementCoul   = fields.Char('VolumeDepassementCoul')
    MontantForfaitFacture   = fields.Char('MontantForfaitFacture')
    MontantDepassementNoirFacture   = fields.Char('MontantDepassementNoirFacture')
    MontantDepassementCoulFacture   = fields.Char('MontantDepassementCoulFacture')
    NumContrat  = fields.Char('NumContrat')
    IdTiersContrat  = fields.Char('IdTiersContrat')
    CompteTiersContrat  = fields.Char('CompteTiersContrat')
    CompteTiersFacture  = fields.Char('CompteTiersFacture')


class LigneFacture(models.Model):
    _name = 'file.ligne.facture'


    Domaine = fields.Char('Domaine')
    IdLigne = fields.Char('IdLigne')
    IdFacture   = fields.Char('IdFacture')
    IdTiers = fields.Char('IdTiers')
    NumFacture  = fields.Char('NumFacture')
    Facture_Avoir   = fields.Char('Facture_Avoir')
    DateFacture = fields.Char('DateFacture')
    IdContrat   = fields.Char('IdContrat')
    NumContrat  = fields.Char('NumContrat')
    AnneeContrat    = fields.Char('AnneeContrat')
    NumeroSerie = fields.Char('NumeroSerie')
    RefArticle  = fields.Char('RefArticle')
    TypeArticle = fields.Char('TypeArticle')
    Designation = fields.Char('Designation')
    PxUnitaire  = fields.Char('PxUnitaire')
    Remise  = fields.Char('Remise')
    PxUnitaireNet   = fields.Char('PxUnitaireNet')
    Qte = fields.Char('Qte')
    TotalHT = fields.Char('TotalHT')
    IdTiersContrat  = fields.Char('IdTiersContrat')
    CompteTiersContrat  = fields.Char('CompteTiersContrat')
    CompteTiersFacture  = fields.Char('CompteTiersFacture')
    DatePeriodeDebut    = fields.Char('DatePeriodeDebut')
    DatePeriodeFin  = fields.Char('DatePeriodeFin')


class BL(models.Model):
    _name = 'file.bl'


    Domaine = fields.Char('Domaine')
    IdTiers = fields.Char('IdTiers')
    AnneeContrat    = fields.Char('AnneeContrat')
    TypePiece   = fields.Char('TypePiece')
    TypeFacture = fields.Char('TypeFacture')
    NumPiece    = fields.Char('NumPiece')
    DatePiece   = fields.Char('DatePiece')
    DateEcheance    = fields.Char('DateEcheance')
    TotalHT = fields.Char('TotalHT')
    TotalTVA    = fields.Char('TotalTVA')
    TotalTTC    = fields.Char('TotalTTC')
    NumReleve   = fields.Char('NumReleve')
    DateReleve  = fields.Char('DateReleve')
    DateDebutPeriode    = fields.Char('DateDebutPeriode')
    DateFinPeriode  = fields.Char('DateFinPeriode')
    CompteurNoir    = fields.Char('CompteurNoir')
    CompteurCoul    = fields.Char('CompteurCoul')
    ConsommationNoir    = fields.Char('ConsommationNoir')
    ConsommationCoul    = fields.Char('ConsommationCoul')
    VolumeDepassementNoir   = fields.Char('VolumeDepassementNoir')
    VolumeDepassementCoul   = fields.Char('VolumeDepassementCoul')
    MontantForfaitFacture   = fields.Char('MontantForfaitFacture')
    MontantDepassementNoirFacture   = fields.Char('MontantDepassementNoirFacture')
    MontantDepassementCoulFacture   = fields.Char('MontantDepassementCoulFacture')
    NumContrat  = fields.Char('NumContrat')
    IdTiersContrat  = fields.Char('IdTiersContrat')
    CompteTiersContrat  = fields.Char('CompteTiersContrat')
    CompteTiersFacture  = fields.Char('CompteTiersFacture')


class BLLigne(models.Model):
    _name = 'file.bl.ligne'

    Domaine = fields.Char('Domaine')
    IdLigne = fields.Char('IdLigne')
    IdPiece = fields.Char('IdPiece')
    IdTiers = fields.Char('IdTiers')
    NumPiece    = fields.Char('NumPiece')
    TypePiece   = fields.Char('TypePiece')
    DatePiece   = fields.Char('DatePiece')
    IdContrat   = fields.Char('IdContrat')
    NumContrat  = fields.Char('NumContrat')
    AnneeContrat    = fields.Char('AnneeContrat')
    NumeroSerie = fields.Char('NumeroSerie')
    RefArticle  = fields.Char('RefArticle')
    TypeArticle = fields.Char('TypeArticle')
    Designation = fields.Char('Designation')
    PxUnitaire  = fields.Char('PxUnitaire')
    Remise  = fields.Char('Remise')
    PxUnitaireNet   = fields.Char('PxUnitaireNet')
    Qte = fields.Char('Qte')
    TotalHT = fields.Char('TotalHT')
    DatePeriodeDebut    = fields.Char('DatePeriodeDebut')
    DatePeriodeFin  = fields.Char('DatePeriodeFin')


class Machine(models.Model):
    _name = 'file.machine'


    @api.multi
    def _compute_contrat(self):
        for rec in self:
            contrat_id = self.env['file.contrat'].search([('NumeroSerie','=',self.NumeroSerie)])
            self.contrat_id = contrat_id.ids

            compteur_id = self.env['file.compteur'].search([('NumeroSerie','=',self.NumeroSerie)])
            self.compteur_id = compteur_id.ids
            
            releve_id = self.env['file.releve'].search([('NumeroSerie','=',self.NumeroSerie)])
            self.releve_id = releve_id.ids
            
            # fatcure_id = self.env['file.fatcure'].search([('NumeroSerie','=',self.NumeroSerie)])
            # self.fatcure_id = fatcure_id.ids
            
            facture_line_id = self.env['file.ligne.facture'].search([('NumeroSerie','=',self.NumeroSerie)])
            self.facture_line_id = facture_line_id.ids

            bl_line_id = self.env['file.bl.ligne'].search([('NumeroSerie','=',self.NumeroSerie)])
            self.bl_line_id = bl_line_id.ids


    NumeroSerie = fields.Char('NumeroSerie')

    contrat_id = fields.Many2many('file.contrat', compute='_compute_contrat')
    compteur_id = fields.Many2many('file.compteur', compute='_compute_contrat')
    releve_id  = fields.Many2many('file.releve', compute='_compute_contrat')
    facture_id  = fields.Many2many('file.fatcure', compute='_compute_contrat')
    facture_line_id  = fields.Many2many('file.ligne.facture', compute='_compute_contrat')
    bl_line_id  = fields.Many2many('file.bl.ligne', compute='_compute_contrat')

