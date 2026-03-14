import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { AddInfoPopup } from "@tgr_l10n_sv_edi_pos/app/add_info_popup/add_info_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";

patch(PosStore.prototype, {
  // @Override
  async processServerData() {
    await super.processServerData();
    if (this.isSalvadorianCompany()) {
      // this["res.city"] = this.data["res.city"];
      // this["l10n_latam.identification.type"] =
      //   this.data["l10n_latam.identification.type"];
      // this["l10n_sv.res.city.district"] =
      //   this.data["l10n_sv.res.city.district"];
      // this.l10n_latam_document_type =
      //   this.data.custom["l10n_latam_document_type"];
    }
  },
  isSalvadorianCompany() {
    return this.company.country_id?.code == "SV";
  },
  createNewOrder() {
    const order = super.createNewOrder(...arguments);

    if (this.isSalvadorianCompany() && !order.partner_id) {
      order.update({ partner_id: this.session._consumidor_final_anonimo_id });
    }

    return order;
  },

  async addL10nSvEdiFields(order) {
    const payload = await makeAwaitable(this.dialog, AddInfoPopup, { order });
    if (payload) {
      console.log("payload", payload);
      order.l10n_latam_document_type_code = payload.l10n_latam_document_type;
      return true;
    }
    return false;
  },
  getReceiptHeaderData(order) {
    const result = super.getReceiptHeaderData(...arguments);
    if (!this.isSalvadorianCompany() || !order) {
      return result;
    }
    console.log("this", this);
    result.company.sv_vat = this.company.vat;
    result.receipt_header = this.config.l10n_sv_edi_receipt_header;
    result.partner = order.get_partner();
    result.sv_doc_type = order.l10n_latam_document_type_code;
    console.log("result", result);
    return result;
  },
});
