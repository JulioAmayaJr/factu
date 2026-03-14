/** @odoo-module */

import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useState } from "@odoo/owl";

export class AddInfoPopup extends Component {
  static template = "tgr_l10n_sv_edi_pos.AddInfoPopup";
  static components = { Dialog };
  static props = {
    order: Object,
    getPayload: Function,
    close: Function,
  };
  setup() {
    this.pos = usePos();
    const order = this.props.order;
    this.state = useState({
      l10n_latam_document_type: order.l10n_latam_document_type_code || "01",
    });
  }
  confirm() {
    this.props.getPayload(this.state);
    this.props.close();
  }
}
