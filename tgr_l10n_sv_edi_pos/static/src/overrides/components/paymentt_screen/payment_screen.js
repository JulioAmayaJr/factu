/** @odoo-module */

import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

import { Component, useState } from "@odoo/owl";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
  setup() {
    super.setup(...arguments);
    this.state = useState({
      l10n_latam_document_type_code: "01",
    });
  },
  //@override
  async toggleIsToInvoice() {
    if (
      this.pos.company.country_id?.code === "SV" &&
      !this.currentOrder.is_to_invoice()
    ) {
      const addedSvFields = await this.pos.addL10nSvEdiFields(
        this.currentOrder,
      );
      if (!addedSvFields) {
        this.currentOrder.set_to_invoice(!this.currentOrder.is_to_invoice());
      }
    }
    super.toggleIsToInvoice(...arguments);
  },

  onDocumentTypeChange(ev) {
    const selectCode = ev.target.value;
    order = this.currentOrder;
    this.state.l10n_latam_document_type_code = selectCode;
    order.l10n_latam_document_type_code =
      this.state.l10n_latam_document_type_code;
    console.log(this.state.l10n_latam_document_type_code);
  },
  areSvFieldsVisible() {
    return (
      this.pos.company.country_id?.code === "SV" &&
      this.currentOrder.is_to_invoice()
    );
  },
  async _isOrderValid(isForceValidate) {
    const res = await super._isOrderValid(...arguments);
    if (!this.pos.isSalvadorianCompany() && res) {
      return res;
    }
    if (!res) {
      return false;
    }
    // const currentPartner = this.currentOrder.get_partner();
    // if (currentPartner && !currentPartner.vat) {
    //   this.pos.editPartner(currentPartner);
    //   this.dialog.add(AlertDialog, {
    //     title: _t("Campo Faltante"),
    //     body: _t("Se Requiere un Número de Identificación"),
    //   });
    //   return false;
    // }
    return res;
  },
});
