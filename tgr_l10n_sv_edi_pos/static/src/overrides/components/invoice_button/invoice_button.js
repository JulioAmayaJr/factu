/** @odoo-module */

import { InvoiceButton } from "@point_of_sale/app/screens/ticket_screen/invoice_button/invoice_button";
import { AddInfoPopup } from "@tgr_l10n_sv_edi_pos/app/add_info_popup/add_info_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { patch } from "@web/core/utils/patch";

patch(InvoiceButton.prototype, {
  async onWillInvoiceOrder(order, newPartner) {
    if (this.pos.company.country_id?.code !== "SV") {
      return true;
    }
    const payload = await makeAwaitable(this.dialog, AddInfoPopup, {
      order,
    });
    if (payload) {
      order.l10n_latam_document_type = payload.l10n_latam_document_type;
      await this.pos.data.ormWrite("pos.order", [order.id], {
        l10n_latam_document_type_code: order.l10n_latam_document_type,
      });
      console.log(payload);
    }
    return Boolean(payload);
  },
});
