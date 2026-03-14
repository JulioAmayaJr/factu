import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
  setup(vals) {
    super.setup(...arguments);
  },

  isSalvadorianCompany() {
    return this.company.country_id?.code == "SV";
  },

  export_for_printing(baseUrl, headerData) {
    const result = super.export_for_printing(...arguments);
    if (!this.isSalvadorianCompany()) {
      return result;
    }
    console.log("this", this);
    return {
      ...result,
      tgr_l10n_sv_edi_codigo_generacion:
        this.account_move?.tgr_l10n_sv_edi_codigo_generacion,
      tgr_l10n_sv_edi_numero_control:
        this.account_move?.tgr_l10n_sv_edi_numero_control,
      tgr_l10n_sv_edi_sello_recibido:
        this.account_move?.tgr_l10n_sv_edi_sello_recibido,
      tgr_l10n_sv_edi_barcode_image:
        this.account_move?.tgr_l10n_sv_edi_barcode_image,
      l10n_sv_edi_receipt_header: this.config_id?.l10n_sv_edi_receipt_header,
    };
  },
});
