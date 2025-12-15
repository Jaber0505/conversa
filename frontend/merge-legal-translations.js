#!/usr/bin/env node

/**
 * Script pour fusionner les traductions légales dans les fichiers de traduction principaux
 * Usage: node merge-legal-translations.js
 */

const fs = require('fs');
const path = require('path');

const I18N_DIR = path.join(__dirname, 'src', 'assets', 'i18n');

console.log('🔄 Fusion des traductions légales...\n');

try {
  // Lire le fichier légal français
  const legalFrPath = path.join(I18N_DIR, 'legal-fr.json');
  const legalFr = JSON.parse(fs.readFileSync(legalFrPath, 'utf8'));

  // Lire le fichier principal français
  const frPath = path.join(I18N_DIR, 'fr.json');
  const fr = JSON.parse(fs.readFileSync(frPath, 'utf8'));

  // Fusionner
  fr.legal = legalFr.legal;

  // Sauvegarder
  fs.writeFileSync(frPath, JSON.stringify(fr, null, 2), 'utf8');
  console.log('✅ Traductions françaises fusionnées dans fr.json');

  // Ajouter les clés de base dans en.json et nl.json
  const enPath = path.join(I18N_DIR, 'en.json');
  const nlPath = path.join(I18N_DIR, 'nl.json');

  const en = JSON.parse(fs.readFileSync(enPath, 'utf8'));
  const nl = JSON.parse(fs.readFileSync(nlPath, 'utf8'));

  // Ajouter seulement les clés de base (à traduire manuellement ensuite)
  if (!en.legal) {
    en.legal = {
      privacy_policy: "Privacy Policy",
      terms_of_service: "Terms of Service",
      last_updated: "Last updated: {{date}}",
      contact: {
        title: "Contact",
        text: "For any questions about this policy, please contact us:",
        terms_text: "For any questions about these terms, please contact us:",
        address: "Address:"
      }
    };
    fs.writeFileSync(enPath, JSON.stringify(en, null, 2), 'utf8');
    console.log('✅ Clés de base ajoutées dans en.json (traduction manuelle requise)');
  }

  if (!nl.legal) {
    nl.legal = {
      privacy_policy: "Privacybeleid",
      terms_of_service: "Gebruiksvoorwaarden",
      last_updated: "Laatst bijgewerkt: {{date}}",
      contact: {
        title: "Contact",
        text: "Voor vragen over dit beleid kunt u contact met ons opnemen:",
        terms_text: "Voor vragen over deze voorwaarden kunt u contact met ons opnemen:",
        address: "Adres:"
      }
    };
    fs.writeFileSync(nlPath, JSON.stringify(nl, null, 2), 'utf8');
    console.log('✅ Clés de base ajoutées dans nl.json (traduction manuelle requise)');
  }

  console.log('\n🎉 Fusion terminée avec succès !');
  console.log('\n⚠️  IMPORTANT :');
  console.log('  - Les traductions françaises sont complètes');
  console.log('  - Les traductions anglaises et néerlandaises contiennent seulement les clés de base');
  console.log('  - Vous devez traduire manuellement le contenu complet dans en.json et nl.json');
  console.log('  - Utilisez legal-fr.json comme référence pour la structure\n');

} catch (error) {
  console.error('❌ Erreur:', error.message);
  process.exit(1);
}
