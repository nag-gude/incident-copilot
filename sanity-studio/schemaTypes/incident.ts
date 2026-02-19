import { defineField, defineType } from 'sanity'

/**
 * Incident document type for Incident Copilot "Similar past incidents".
 * Knowledge service GROQ expects: _type == "incident", service, rootCause
 */
export const incidentType = defineType({
  name: 'incident',
  title: 'Incident',
  type: 'document',
  fields: [
    defineField({
      name: 'service',
      type: 'string',
      title: 'Service',
      description: 'e.g. api-gateway, ingestion, recommendation',
    }),
    defineField({
      name: 'rootCause',
      type: 'text',
      title: 'Root cause',
      description: 'Root cause description (used by similar-incidents GROQ)',
    }),
    defineField({
      name: 'incidentId',
      type: 'string',
      title: 'Incident ID',
      description: 'Optional reference to Incident Copilot incident ID',
    }),
  ],
})
