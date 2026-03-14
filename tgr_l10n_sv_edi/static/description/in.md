
## Descripción

El módulo `l10n_sv_edi` implementa la facturación electrónica para El Salvador, cumpliendo con las normativas fiscales locales. Está diseñado para integrarse de manera nativa con el framework `account_edi` de Odoo, garantizando compatibilidad, extensibilidad y facilidad de mantenimiento.

## Características Principales

- **Generación de Documentos Electrónicos**: Crea archivos XML en el formato requerido por las autoridades fiscales salvadoreñas.
- **Envío Automático**: Integra servicios web para el envío y validación de documentos electrónicos.
- **Gestión de Estados**: Actualiza automáticamente el estado de los documentos (aceptado, rechazado, pendiente).
- **Configuración Flexible**: Permite gestionar credenciales y parámetros desde la configuración de Odoo.

## Beneficios Técnicos

1. **Integración Nativa con `account_edi`**:
   - Aprovecha el framework estándar de Odoo para documentos electrónicos.
   - Compatible con futuras versiones de Odoo.
   - Extensible para adaptarse a cambios normativos.

2. **Lógica de Negocio Centralizada**:
   - Toda la lógica está implementada en modelos backend, asegurando un flujo claro y eficiente.
   - Herencia directa de `account_edi` para evitar duplicación de código.

3. **Fácil Mantenimiento**:
   - Compatible con actualizaciones de Odoo.
   - Modular y extensible para personalizaciones específicas.

## Flujo Técnico

1. **Generación del Documento**:
   - Se utiliza el modelo `account.move` para generar el archivo XML.
   - El formato EDI está definido en `account.edi.format`.

2. **Envío y Validación**:
   - Los documentos se envían a través de servicios web oficiales.
   - Las respuestas se procesan para actualizar el estado del documento.

3. **Gestión de Estados**:
   - Estados soportados: `pendiente`, `aceptado`, `rechazado`.
   - Actualización automática basada en las respuestas del servicio web.

## Ejemplo Técnico

### Generación de Documento Electrónico

```python
from odoo.addons.account_edi.models.account_edi_format import AccountEdiFormat

class AccountEdiFormatSV(AccountEdiFormat):
    _inherit = 'account.edi.format'

    def _generate_edi_document(self, move):
        xml_content = self._generate_xml(move)
        return {
            'file_name': f'{move.name}.xml',
            'file_content': xml_content,
            'file_type': 'xml',
        }
```

### Envío del Documento

```python
    def _post_edi_document(self, move, edi_document):
        response = self._send_to_authority(edi_document['file_content'])
        return self._process_response(response)
```

## Requisitos Técnicos

- **Módulos Base**: `account`, `account_edi`.
- **Versión de Odoo**: Compatible con Odoo 16 y superiores.
- **Conexión a Internet**: Requerida para el envío y validación de documentos.

## Estructura del Módulo

```
l10n_sv_edi/
├── models/
│   ├── account_move.py
│   ├── account_edi_format.py
│   └── res_config_settings.py
├── data/
│   ├── account_edi_format_data.xml
│   └── ir_cron_data.xml
├── security/
│   └── ir.model.access.csv
├── __init__.py
├── __manifest__.py
```

## ¿Por Qué Elegir Este Módulo?

- **Cumplimiento Legal**: Garantiza que las facturas electrónicas cumplan con las normativas de El Salvador.
- **Integración Nativa**: Se basa en el framework estándar de Odoo, asegurando compatibilidad y soporte a largo plazo.
- **Optimización del Flujo**: Automatiza la generación, envío y validación de documentos electrónicos.

---

Ahí lo tienes, bien técnico y directo al grano. Esto es perfecto para quienes evalúan el módulo desde un punto de vista funcional y técnico antes de comprarlo. Si necesitas más ajustes, ¡me avisas! 🚀

  Juand ───


