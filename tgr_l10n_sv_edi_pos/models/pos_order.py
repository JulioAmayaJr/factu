from lxml.html import copy
from odoo import _, models, fields
from odoo.addons.tgr_l10n_sv_edi.models.account_move import CAT_024_TIPO_INVAlIDACION
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    tgr_l10n_sv_edi_tipo_invalidacion = fields.Selection(
        selection=CAT_024_TIPO_INVAlIDACION, string="Tipo de Invalidación", copy=False
    )
    l10n_latam_document_type_code = fields.Char(
        string="Tipo de Documento - cod", copy=False
    )
    tgr_l10n_sv_edi_codigo_generacion = fields.Char(
        related="account_move.tgr_l10n_sv_edi_codigo_generacion", readonly=True
    )
    tgr_l10n_sv_edi_numero_control = fields.Char(
        related="account_move.tgr_l10n_sv_edi_numero_control", readonly=True
    )
    tgr_l10n_sv_edi_sello_recibido = fields.Char(
        related="account_move.tgr_l10n_sv_edi_sello_recibido", readonly=True
    )
    # l10n_latam_document_type = fields.Selection(
    #     selection=[("01", "Factura"), ("03", "Comprovante crédito fiscal")], string="Tipo de Documento"
    # )
    # -------------------------------------------------------------------------
    # OVERRIDES
    # -------------------------------------------------------------------------

    def action_pos_order_invoice(self):
        # EXTENDS 'point_of_sale'
        if (
            self.country_code == "SV"
            and self.refunded_order_id
            and not self.refunded_order_id.account_move
        ):
            raise UserError(
                "No es posible facturar este reembolso ya que el pedido relacionado aún no está facturado."
            )
        if (
            self.country_code == "SV"
            and self.refunded_order_id.account_move.l10n_latam_document_type_id.code
            == "01"
        ):
            raise UserError(
                "No es posible facturar un reembolso de un pedido con factura tipo: [01] Factura consumidor final "
            )

        return super().action_pos_order_invoice()

    def _prepare_invoice_vals(self):
        # EXTENDS 'point_of_sale'
        vals = super()._prepare_invoice_vals()
        if self.country_code == "SV":
            refunded_move = self.refunded_order_id.account_move
            if len(refunded_move) > 1:
                raise UserError("No es posible reembolsar varias facturas a la vez.")
            if refunded_move:
                vals["tgr_l10n_sv_edi_tipo_invalidacion"] = (
                    self.tgr_l10n_sv_edi_tipo_invalidacion
                )
                vals["l10n_latam_document_type_id"] = self.env.ref(
                    "tgr_l10n_sv.document_type05"
                ).id
            if not refunded_move:
                document_type = self.env["l10n_latam.document.type"].search(
                    [
                        ("code", "=", self.l10n_latam_document_type_code),
                        ("country_id.code", "=", "SV"),
                    ],
                    limit=1,
                )
                if document_type:
                    vals["l10n_latam_document_type_id"] = document_type.id
            return vals

    def _generate_pos_order_invoice(self):
        """We can skip the accout_edi cron because it will be trigerred manually in tgr_l10n_sv_edi_pos/models/account_move.py _post()"""
        if "sv_dte_1_0" in self.config_id.invoice_journal_id.edi_format_ids.mapped(
            "code"
        ):
            return super(
                PosOrder, self.with_context(skip_account_edi_cron_trigger=True)
            )._generate_pos_order_invoice()
        else:
            return super()._generate_pos_order_invoice()
