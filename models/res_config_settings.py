# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval

from odoo import api, fields, models
from odoo.exceptions import MissingError, AccessError, ValidationError
import os
import getpass


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    

    mounted_path                    = fields.Char(string='Mounted path', default='/', required=True)
    statement_file_name             = fields.Char(string='Statement file name', default='Releves.txt', required=True)
    counter_file_name               = fields.Char(string='Counter file name', default='Compteurs.txt', required=True)
    contract_file_name              = fields.Char(string='Contract file name', default='Contrats.txt', required=True)
    invoice_line_file_name          = fields.Char(string='Invoice line file name', default='FacturesLignes.txt', required=True)
    invoice_file_name               = fields.Char(string='Invoice file name', default='Factures.txt', required=True)
    picking_line_file_name          = fields.Char(string='Picking line file name', default='BLLignes.txt', required=True)

    machine_serial_number           = fields.Char(string='N° Série Machine', required=True)
    black_white_counter             = fields.Char(string='Releve NB', required=True)
    color_counter                   = fields.Char(string='Releve COUL', required=True)
    contract_number                 = fields.Char(string='N° Contrat', required=True)
    black_white_cost                = fields.Char(string='Coût Page NB', required=True)
    color_cost                      = fields.Char(string='Coût page COUL', required=True)
    total_ttc                       = fields.Char(string='Engagement Total facture', required=True)
    last_statement_date             = fields.Char(string='Date dernier relevé', required=True)
    last_auto_update_date           = fields.Char(string='Date dernier mise à jour automatique', required=True)
    contract_periode                = fields.Char(string='Durée contrat', required=True)


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        res.update(
            mounted_path=ICPSudo.get_param('passerelle.mounted_path') or '/mnt/windows/',
            statement_file_name= ICPSudo.get_param('passerelle.statement_file_name') or 'Releves.txt',
            counter_file_name= ICPSudo.get_param('passerelle.counter_file_name') or 'Compteurs.txt',
            contract_file_name= ICPSudo.get_param('passerelle.contract_file_name') or 'Contrats.txt',
            invoice_line_file_name= ICPSudo.get_param('passerelle.invoice_line_file_name') or 'FacturesLignes.txt',
            invoice_file_name= ICPSudo.get_param('passerelle.invoice_file_name') or 'Factures.txt',
            picking_line_file_name= ICPSudo.get_param('passerelle.picking_line_file_name') or 'BLLignes.txt',
            

            machine_serial_number= ICPSudo.get_param('passerelle.machine_serial_number') or 'x_studio_field_Y3N9k',
            color_counter= ICPSudo.get_param('passerelle.color_counter') or 'x_studio_field_vijGj',
            black_white_counter= ICPSudo.get_param('passerelle.black_white_counter') or 'x_studio_field_vnBQI',
            contract_number= ICPSudo.get_param('passerelle.contract_number') or 'x_studio_field_3pGKT',
            color_cost= ICPSudo.get_param('passerelle.color_cost') or 'x_studio_field_dIAeR',
            black_white_cost= ICPSudo.get_param('passerelle.black_white_cost') or 'x_studio_field_qCQvW',
            total_ttc= ICPSudo.get_param('passerelle.total_ttc') or 'x_studio_field_BgSE5',
            last_statement_date= ICPSudo.get_param('passerelle.last_statement_date') or 'x_studio_field_KdJJ4',
            last_auto_update_date= ICPSudo.get_param('passerelle.last_auto_update_date') or 'x_studio_field_rvd5o',
            contract_periode = ICPSudo.get_param('passerelle.contract_periode') or 'x_studio_field_u8HXt',
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.mounted_path and not os.path.isdir(self.mounted_path):
            raise ValidationError('The specified path cannot be located on this system')
        elif not os.access(self.mounted_path, os.R_OK):
            raise AccessError("User %s don't have read permission on the specified directory"%getpass.getuser())
       
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("passerelle.mounted_path", self.mounted_path)
        ICPSudo.set_param("passerelle.statement_file_name", self.statement_file_name)
        ICPSudo.set_param("passerelle.counter_file_name", self.counter_file_name)
        ICPSudo.set_param("passerelle.contract_file_name", self.contract_file_name)
        ICPSudo.set_param("passerelle.invoice_line_file_name", self.invoice_line_file_name)
        ICPSudo.set_param("passerelle.invoice_file_name", self.invoice_file_name)
        ICPSudo.set_param("passerelle.picking_line_file_name", self.picking_line_file_name)


        ICPSudo.set_param('passerelle.machine_serial_number', self.machine_serial_number)
        ICPSudo.set_param('passerelle.color_counter', self.color_counter)
        ICPSudo.set_param('passerelle.black_white_counter', self.black_white_counter)
        ICPSudo.set_param('passerelle.contract_number', self.contract_number)
        ICPSudo.set_param('passerelle.color_cost', self.color_cost)
        ICPSudo.set_param('passerelle.black_white_cost', self.black_white_cost)
        ICPSudo.set_param('passerelle.total_ttc', self.total_ttc)
        ICPSudo.set_param('passerelle.last_statement_date', self.last_statement_date)
        ICPSudo.set_param('passerelle.last_auto_update_date', self.last_auto_update_date)
        ICPSudo.set_param('passerelle.contract_periode', self.contract_periode)
        