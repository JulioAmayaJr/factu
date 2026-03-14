from odoo import models


class MixinDteDocument(models.AbstractModel):
    _inherit = "l10n_sv.dte.mixin"

    def _get_cod_pos(self, invoice):
        pos_config = self.env["pos.order"].search([("name", "=", invoice.ref)], limit=1)
        pos_config = pos_config.config_id if pos_config else None
        res = {}
        if pos_config:
            res["codPuntoVentaMH"] = pos_config.l10n_sv_edi_cod_pos_mh or "0000"
            res["codPuntoVenta"] = pos_config.l10n_sv_edi_cod_pos or "0001"
        return res


class CcfDteDocument(models.AbstractModel):
    _inherit = "l10n_sv.dte.ccf"

    def _get_emisor(self, invoice):
        res = super()._get_emisor(invoice)
        cod_pos = self._get_cod_pos(invoice)
        return {**res, **cod_pos}


class DteAnulacion(models.AbstractModel):
    _inherit = "l10n_sv.dte.anulacion"

    def _get_emisor(self, invoice):
        res = super()._get_emisor(invoice)
        cod_pos = self._get_cod_pos(invoice)
        return {**res, **cod_pos}


class CfDteDocument(models.AbstractModel):
    _inherit = "l10n_sv.dte.cf"

    def _get_emisor(self, invoice):
        res = super()._get_emisor(invoice)
        cod_pos = self._get_cod_pos(invoice)
        return {**res, **cod_pos}
