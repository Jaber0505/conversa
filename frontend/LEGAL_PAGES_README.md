# Pages Légales - Instructions d'installation

## ✅ Ce qui a été créé

### 1. Composants Angular
- `privacy-policy.component.ts/html/scss` - Politique de confidentialité
- `terms-of-service.component.ts/html/scss` - Conditions d'utilisation

### 2. Routes ajoutées
- `/fr/privacy-policy` - Politique de confidentialité
- `/en/privacy-policy` - Privacy Policy
- `/nl/privacy-policy` - Privacybeleid
- `/fr/terms-of-service` - Conditions d'utilisation
- `/en/terms-of-service` - Terms of Service
- `/nl/terms-of-service` - Gebruiksvoorwaarden

### 3. Footer mis à jour
Le footer contient maintenant 4 liens :
- À propos / About / Over ons
- FAQ
- **Politique de confidentialité** (nouveau)
- **Conditions d'utilisation** (nouveau)

## 📝 Étape importante : Intégrer les traductions

### Option 1 : Copier-coller manuel

Le fichier `legal-fr.json` contient toutes les traductions françaises.

1. Ouvrez `src/assets/i18n/fr.json`
2. Ajoutez le contenu du fichier `legal-fr.json` (fusionnez l'objet `legal` dans le JSON principal)
3. Répétez pour `en.json` et `nl.json` avec les traductions appropriées

### Option 2 : Script automatique (recommandé)

Créez un script Node.js pour fusionner automatiquement :

```javascript
const fs = require('fs');
const path = require('path');

const legalFr = JSON.parse(fs.readFileSync('./src/assets/i18n/legal-fr.json'));
const mainFr = JSON.parse(fs.readFileSync('./src/assets/i18n/fr.json'));

// Fusionner
mainFr.legal = legalFr.legal;

// Sauvegarder
fs.writeFileSync('./src/assets/i18n/fr.json', JSON.stringify(mainFr, null, 2));
console.log('✅ Traductions françaises fusionnées !');
```

## 📄 Contenu des pages

### Politique de confidentialité
Couvre :
- ✅ Données collectées (compte, réservations, techniques)
- ✅ Utilisation des données
- ✅ Base légale RGPD
- ✅ Partage des données (Stripe, partenaires, autorités)
- ✅ **Droits RGPD complets** (accès, rectification, effacement, portabilité, opposition, limitation, réclamation)
- ✅ Conservation des données
- ✅ Sécurité (HTTPS, bcrypt, contrôle d'accès)
- ✅ **Politique de remboursement détaillée**
- ✅ Cookies
- ✅ Modifications

### Conditions d'utilisation
Couvre :
- ✅ Acceptation des conditions
- ✅ Description du service
- ✅ Inscription (18 ans minimum)
- ✅ **Réservations et paiements** (Stripe, PCI-DSS)
- ✅ **Annulation et remboursement** (utilisateur, organisateur, suppression de compte)
- ✅ Jeu interactif (⚠️ connexion Internet requise)
- ✅ Obligations de l'utilisateur
- ✅ Contenu utilisateur
- ✅ Propriété intellectuelle
- ✅ Limitation de responsabilité
- ✅ Suspension et résiliation
- ✅ Loi applicable (droit belge)

## 🌍 Traductions manquantes

Vous devez créer les traductions pour :
- **Anglais** (`en.json`) - Traduisez le contenu de `legal-fr.json`
- **Néerlandais** (`nl.json`) - Traduisez le contenu de `legal-fr.json`

## 🎨 Design

Les pages utilisent :
- Typographie claire et lisible
- Sections avec bordures colorées
- Sections en surbrillance pour les informations importantes (droits RGPD, paiements, annulations)
- Avertissements visuels (bannières jaunes)
- Responsive (mobile-friendly)

## 🔗 Liens footer

Les liens sont relatifs :
- `./privacy-policy` → `/fr/privacy-policy` (selon la langue courante)
- `./terms-of-service` → `/fr/terms-of-service`

## ✉️ Coordonnées de contact

À mettre à jour dans les traductions :
- Email privacy : `privacy@conversa.app`
- Email légal : `legal@conversa.app`
- Adresse : Bruxelles, Belgique

## 🚀 Pour tester

1. Démarrez l'application : `npm start`
2. Allez sur http://localhost:4200
3. Scrollez en bas de page
4. Cliquez sur "Politique de confidentialité" ou "Conditions d'utilisation"
5. Vérifiez que le contenu s'affiche correctement

## ⚖️ Conformité juridique

Ces pages sont conformes :
- ✅ RGPD (Règlement Général sur la Protection des Données)
- ✅ Transparence complète sur le traitement des données
- ✅ Politique de remboursement claire
- ✅ Droits des utilisateurs explicites
- ✅ Bases légales du traitement
- ✅ Coordonnées de contact

**Note importante** : Ces pages constituent un bon point de départ, mais il est recommandé de les faire réviser par un avocat spécialisé en droit numérique pour assurer une conformité complète avec la législation belge et européenne.
