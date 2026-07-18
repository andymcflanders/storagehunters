/**
 * User Guide documentation content.
 *
 * Each section's body is keyed by ISO language code. The renderer picks
 * the user's locale and falls back to English when a translation is
 * missing — adding a new language only requires appending a key here,
 * not changing the interface.
 */

export interface DocSection {
	id: string;
	titleKey: string;
	content: Record<string, string>;
}

export const userGuideSections: DocSection[] = [
	{
		id: 'introduction',
		titleKey: 'docs.userGuide.introduction.title',
		content: {
			en: `
## Welcome to StorageHub

StorageHub is a powerful home inventory management application that helps you organize, track, and find your belongings with ease. Whether you're managing a single closet or an entire household, StorageHub provides the tools you need to stay organized.

### Key Features

- **Hierarchical Organization**: Organize items using Locations, Containers, and Items
- **AI-Powered Classification**: Automatically categorize items using photos
- **QR Code Integration**: Generate and scan QR codes for quick access
- **Smart Search**: Find anything instantly with intelligent search
- **Sharing**: Share containers with others via secure links
- **Reminders**: Set reminders for seasonal items or maintenance tasks
- **Multi-Language Support**: Available in English and Norwegian

### Getting Started

1. **Create a Location**: Start by adding your first location (e.g., "Home", "Office", "Storage Unit")
2. **Add Containers**: Create containers within locations (boxes, shelves, drawers)
3. **Add Items**: Populate containers with your belongings
4. **Generate QR Codes**: Print labels for physical containers
5. **Search and Find**: Use the search feature to locate items quickly
`,
			no: `
## Velkommen til StorageHub

StorageHub er en kraftig applikasjon for å holde orden på eiendelene dine hjemme — til å organisere, spore og finne ting når du trenger dem. Uansett om du har ett skap eller et helt hus, gir StorageHub deg verktøyene du trenger for å holde orden.

### Hovedfunksjoner

- **Hierarkisk organisering**: Organiser gjenstander i steder, beholdere og gjenstander
- **AI-drevet klassifisering**: La AI kategorisere gjenstander automatisk fra bilder
- **QR-kodeintegrering**: Generer og skann QR-koder for rask tilgang
- **Smart søk**: Finn det du trenger raskt med intelligent søk
- **Deling**: Del beholdere med andre via sikre lenker
- **Påminnelser**: Sett påminnelser for sesongbaserte gjenstander eller vedlikehold
- **Flerspråklig**: Tilgjengelig på engelsk og norsk

### Kom i gang

1. **Opprett et sted**: Start med å legge til ditt første sted (f.eks. "Hjem", "Kontor", "Lagerrom")
2. **Legg til beholdere**: Opprett beholdere på stedene (esker, hyller, skuffer)
3. **Legg til gjenstander**: Fyll beholderne med eiendelene dine
4. **Generer QR-koder**: Skriv ut etiketter for de fysiske beholderne
5. **Søk og finn**: Bruk søkefunksjonen for å finne gjenstander raskt
`
		}
	},
	{
		id: 'hierarchy',
		titleKey: 'docs.userGuide.hierarchy.title',
		content: {
			en: `
## Understanding the Hierarchy

StorageHub uses a three-level hierarchy to organize your belongings:

### Locations

Locations are the top-level organizational unit. They represent physical places where you store things.

**Examples:**
- Home
- Office
- Garage
- Storage Unit
- Vacation Home

### Containers

Containers exist within locations and can be nested inside other containers. They represent physical storage units.

**Container Types:**
- Box
- Drawer
- Shelf
- Cabinet
- Closet
- Bin
- Basket
- Other

**Nesting Example:**
\`\`\`
Home (Location)
└── Bedroom Closet (Container)
    ├── Top Shelf (Container)
    │   └── Winter Hats (Items)
    └── Bottom Drawer (Container)
        └── Socks (Items)
\`\`\`

### Items

Items are the individual belongings you want to track. Each item belongs to exactly one container.

**Item Properties:**
- Name and description
- Size (e.g. clothing or shoe size)
- Condition (Good, Fair, Damaged, Needs Repair)
- Seasonal classification
- Value estimate
- Owner (household member)
- Tags for categorization
- Photos
`,
			no: `
## Forstå hierarkiet

StorageHub bruker et hierarki i tre nivåer for å organisere eiendelene dine:

### Steder

Steder er det øverste nivået. De representerer fysiske plasser der du oppbevarer ting.

**Eksempler:**
- Hjem
- Kontor
- Garasje
- Lagerrom
- Hytte

### Beholdere

Beholdere ligger på et sted og kan nestes inni andre beholdere. De representerer fysiske oppbevaringsenheter.

**Beholdertyper:**
- Boks
- Skuff
- Hylle
- Skap
- Garderobe
- Kasse
- Kurv
- Annet

**Eksempel på nesting:**
\`\`\`
Hjem (sted)
└── Soveromsgarderobe (beholder)
    ├── Øverste hylle (beholder)
    │   └── Vinterluer (gjenstander)
    └── Nederste skuff (beholder)
        └── Sokker (gjenstander)
\`\`\`

### Gjenstander

Gjenstander er de enkelte eiendelene du vil holde oversikt over. Hver gjenstand tilhører nøyaktig én beholder.

**Egenskaper for gjenstander:**
- Navn og beskrivelse
- Størrelse (f.eks. kles- eller skostørrelse)
- Tilstand (God, Brukbar, Skadet, Trenger reparasjon)
- Sesongklassifisering
- Verdianslag
- Eier (husstandsmedlem)
- Etiketter for kategorisering
- Bilder
`
		}
	},
	{
		id: 'locations',
		titleKey: 'docs.userGuide.locations.title',
		content: {
			en: `
## Managing Locations

Locations are the foundation of your organization system.

### Creating a Location

1. Navigate to the **Locations** page from the main navigation
2. Click **Add Location**
3. Enter a name (required) and optional address/description
4. Click **Create**

### Editing a Location

1. Navigate to the location you want to edit
2. Click the **Edit** button (pencil icon)
3. Modify the name or address
4. Click **Save**

### Deleting a Location

> **Warning:** Deleting a location will also delete all containers and items within it. This action cannot be undone.

1. Navigate to the location
2. Click the **Delete** button
3. Confirm the deletion in the dialog

### Location Overview

Each location page shows:
- Total number of containers
- Total number of items
- List of top-level containers
- Recent activity
`,
			no: `
## Administrere steder

Steder er grunnlaget for organiseringssystemet ditt.

### Opprette et sted

1. Gå til **Steder**-siden i hovedmenyen
2. Klikk **Legg til sted**
3. Skriv inn et navn (obligatorisk) og valgfri adresse eller beskrivelse
4. Klikk **Opprett**

### Redigere et sted

1. Gå til stedet du vil redigere
2. Klikk **Rediger**-knappen (blyantikonet)
3. Endre navnet eller adressen
4. Klikk **Lagre**

### Slette et sted

> **Advarsel:** Når du sletter et sted, slettes også alle beholdere og gjenstander i det. Dette kan ikke angres.

1. Gå til stedet
2. Klikk **Slett**-knappen
3. Bekreft slettingen i dialogen

### Stedsoversikt

Hver stedsside viser:
- Totalt antall beholdere
- Totalt antall gjenstander
- Liste over beholdere på toppnivå
- Nylig aktivitet
`
		}
	},
	{
		id: 'containers',
		titleKey: 'docs.userGuide.containers.title',
		content: {
			en: `
## Working with Containers

Containers are versatile storage units that can hold items or other containers.

### Creating a Container

1. Navigate to a location or parent container
2. Click **Add Container**
3. Enter a name and select a type
4. Optionally add a description
5. Click **Create**

### Container Types

Choose the type that best describes your physical container:

| Type | Best For |
|------|----------|
| Box | Cardboard boxes, storage boxes |
| Drawer | Desk drawers, dresser drawers |
| Shelf | Bookshelf shelves, closet shelves |
| Cabinet | Kitchen cabinets, bathroom cabinets |
| Closet | Entire closets as containers |
| Bin | Plastic bins, storage totes |
| Basket | Baskets, hampers |
| Other | Anything that doesn't fit above |

### Nesting Containers

Containers can be nested to any depth. This is useful for complex organization:

1. Navigate to the parent container
2. Click **Add Container**
3. The new container is automatically placed inside the parent

### Moving Containers

To relocate a container:

1. Navigate to the container
2. Click **Move**
3. Select the new parent (location or container)
4. Click **Confirm**

### QR Codes

Each container automatically gets a unique QR code:

1. Navigate to the container
2. Click the **QR Code** button
3. Print or download the QR code
4. Attach it to the physical container

### Container Photos

Give a container a hero image so it's easy to recognize at a glance:

1. Navigate to the container
2. Click **Take Photo** to capture an image with your device's camera
3. The photo is shown at the top of the container page
4. Use **Replace Image** or **Remove Image** to change it later
`,
			no: `
## Jobbe med beholdere

Beholdere er fleksible oppbevaringsenheter som kan inneholde gjenstander eller andre beholdere.

### Opprette en beholder

1. Gå til et sted eller en overordnet beholder
2. Klikk **Legg til beholder**
3. Skriv inn et navn og velg en type
4. Legg eventuelt til en beskrivelse
5. Klikk **Opprett**

### Beholdertyper

Velg typen som best beskriver den fysiske beholderen:

| Type | Best for |
|------|----------|
| Boks | Pappesker, oppbevaringsbokser |
| Skuff | Skrivebordsskuffer, kommodeskuffer |
| Hylle | Bokhyllehyller, garderobehyller |
| Skap | Kjøkkenskap, baderomsskap |
| Garderobe | Hele garderober som beholdere |
| Kasse | Plastkasser, lagringskasser |
| Kurv | Kurver, klesvaskkurver |
| Annet | Alt annet som ikke passer over |

### Neste beholdere

Beholdere kan nestes så dypt du vil. Dette er nyttig for kompleks organisering:

1. Gå til den overordnede beholderen
2. Klikk **Legg til beholder**
3. Den nye beholderen plasseres automatisk inni den overordnede

### Flytte beholdere

For å flytte en beholder:

1. Gå til beholderen
2. Klikk **Flytt**
3. Velg ny overordnet (sted eller beholder)
4. Klikk **Bekreft**

### QR-koder

Hver beholder får automatisk en unik QR-kode:

1. Gå til beholderen
2. Klikk **QR-kode**-knappen
3. Skriv ut eller last ned QR-koden
4. Fest den på den fysiske beholderen

### Beholderbilder

Gi beholderen et hovedbilde så den er lett å kjenne igjen:

1. Gå til beholderen
2. Klikk **Ta bilde** for å ta et bilde med kameraet på enheten
3. Bildet vises øverst på beholdersiden
4. Bruk **Erstatt bilde** eller **Fjern bilde** for å endre det senere
`
		}
	},
	{
		id: 'items',
		titleKey: 'docs.userGuide.items.title',
		content: {
			en: `
## Managing Items

Items are the individual belongings you track in StorageHub.

### Adding an Item

1. Navigate to a container
2. Click **Add Item**
3. Fill in the details:
   - **Name** (required): What is this item?
   - **Description**: Additional details
   - **Size**: Clothing/shoe size or dimensions
   - **Condition**: Current state of the item
   - **Seasonal**: Optional season classification
   - **Value Estimate**: Approximate worth
   - **Owner**: Which household member it belongs to
   - **Tags**: Categorization labels
   - **Photos**: Visual reference

### Adding Photos

Photos help you identify and remember items:

1. While creating/editing an item, click **Add Photo**
2. Take a photo or upload from your device
3. AI automatically classifies the item in the background after upload

### Using Tags

Tags help you categorize and find items:

1. Create tags from the **Tags** page
2. Add tags to items when creating or editing
3. Search by tag to find related items

### Item Conditions

Track the state of your belongings:

- **Good**: Item is in working/normal condition
- **Fair**: Minor wear or issues
- **Damaged**: Significant damage but still usable
- **Needs Repair**: Requires attention before use

### Moving Items

To move an item to a different container:

1. Navigate to the item
2. Click **Move**
3. Select the destination container
4. Click **Confirm**

### Seasonal Items

Mark items as seasonal for easy filtering:
- Spring
- Summer
- Fall
- Winter
- Holiday
`,
			no: `
## Administrere gjenstander

Gjenstander er de enkelte eiendelene du holder oversikt over i StorageHub.

### Legge til en gjenstand

1. Gå til en beholder
2. Klikk **Legg til gjenstand**
3. Fyll inn detaljene:
   - **Navn** (obligatorisk): Hva er dette?
   - **Beskrivelse**: Flere detaljer
   - **Størrelse**: Kles-/skostørrelse eller mål
   - **Tilstand**: Hva er tilstanden?
   - **Sesong**: Valgfri sesongklassifisering
   - **Verdianslag**: Omtrentlig verdi
   - **Eier**: Hvilket husstandsmedlem den tilhører
   - **Etiketter**: Kategorisering
   - **Bilder**: Visuell referanse

### Legge til bilder

Bilder hjelper deg å huske og identifisere gjenstander:

1. Når du oppretter eller redigerer en gjenstand, klikk **Legg til bilde**
2. Ta et bilde eller last opp fra enheten
3. AI klassifiserer gjenstanden automatisk i bakgrunnen etter opplasting

### Bruke etiketter

Etiketter hjelper deg å kategorisere og finne gjenstander:

1. Opprett etiketter fra **Etiketter**-siden
2. Legg til etiketter på gjenstander når du oppretter eller redigerer
3. Søk etter etikett for å finne relaterte gjenstander

### Tilstander

Hold oversikt over tilstanden på eiendelene:

- **God**: I normal/funksjonell tilstand
- **Brukbar**: Mindre slitasje eller feil
- **Skadet**: Betydelig skade men fortsatt brukbar
- **Trenger reparasjon**: Må fikses før bruk

### Flytte gjenstander

For å flytte en gjenstand til en annen beholder:

1. Gå til gjenstanden
2. Klikk **Flytt**
3. Velg målbeholder
4. Klikk **Bekreft**

### Sesongbaserte gjenstander

Marker gjenstander som sesongbaserte for enkel filtrering:
- Vår
- Sommer
- Høst
- Vinter
- Høytid
`
		}
	},
	{
		id: 'ai-features',
		titleKey: 'docs.userGuide.aiFeatures.title',
		content: {
			en: `
## AI Features

StorageHub uses artificial intelligence to help you organize faster and smarter.

### Photo Classification

When you add a photo to an item, AI can automatically:

1. **Identify the item**: Suggest what the item is
2. **Categorize**: Recommend appropriate tags
3. **Describe**: Generate a description

**How to use:**
1. Click **Add Photo** when creating an item
2. Take or upload a photo
3. Classification runs automatically in the background after upload
4. Review the suggested name, description, and tags once processing finishes

### AI Owner Suggestion

When classifying a photo, the AI can also guess which household member an
item most likely belongs to, based on the item's size or motif and each
member's age and gender:

- The guess appears as a suggestion banner on the item detail page
- It is never applied automatically — click to accept it as the owner,
  or dismiss it
- Add birthdate and gender to household members to improve suggestions

### AI-Generated Summaries

AI can summarize a container's contents on printed labels:

1. When printing a label, choose the template with an AI summary
2. A brief overview of the container's contents is generated for the
   label preview and printout

### Configuration

Administrators can configure AI settings:

- Enable/disable AI features
- Choose AI models from a fixed list (e.g. GPT-4o, GPT-4o Mini)
- Set the API key

See the Admin Features section for details.
`,
			no: `
## AI-funksjoner

StorageHub bruker kunstig intelligens for å hjelpe deg å organisere raskere og smartere.

### Bildeklassifisering

Når du legger til et bilde av en gjenstand, kan AI automatisk:

1. **Identifisere gjenstanden**: Foreslå hva det er
2. **Kategorisere**: Anbefale passende etiketter
3. **Beskrive**: Generere en beskrivelse

**Slik bruker du det:**
1. Klikk **Legg til bilde** når du oppretter en gjenstand
2. Ta eller last opp et bilde
3. Klassifiseringen kjører automatisk i bakgrunnen etter opplasting
4. Se gjennom foreslått navn, beskrivelse og etiketter når prosesseringen er ferdig

### AI-eierforslag

Når et bilde klassifiseres, kan AI-en også gjette hvilket husstandsmedlem
gjenstanden mest sannsynlig tilhører, basert på størrelse eller motiv og
hvert medlems alder og kjønn:

- Forslaget vises som et banner på gjenstandens detaljside
- Det brukes aldri automatisk — klikk for å godta det som eier,
  eller avvis det
- Legg inn fødselsdato og kjønn på husstandsmedlemmene for bedre forslag

### AI-genererte sammendrag

AI kan oppsummere innholdet i en beholder på utskrevne etiketter:

1. Når du skriver ut en etikett, velg malen med AI-sammendrag
2. En kort oppsummering av beholderens innhold genereres for
   forhåndsvisningen og utskriften

### Konfigurasjon

Administratorer kan konfigurere AI-innstillinger:

- Aktivere/deaktivere AI-funksjoner
- Velge AI-modeller fra en fast liste (f.eks. GPT-4o, GPT-4o Mini)
- Sette API-nøkkelen

Se Admin-funksjoner for detaljer.
`
		}
	},
	{
		id: 'searching',
		titleKey: 'docs.userGuide.searching.title',
		content: {
			en: `
## Searching

StorageHub provides powerful search capabilities to help you find anything quickly.

### Quick Search

The search bar in the header provides instant results:

1. Click the search bar
2. Type your search query
3. Results appear as you type
4. Click a result to navigate directly to it

### Search Page

For advanced searching, visit the dedicated Search page:

1. Click **Search** in the navigation
2. Enter your search terms
3. Use filters to narrow results

### What You Can Search

Search returns items. Your query matches against:

- Item names and descriptions
- Tags and AI-generated tags
- Size
- Where the item is stored

### Search Tips

- Use specific terms for better results
- Search for tags using the tag name
- Partial words work (e.g., "win" finds "winter")
- Search is case-insensitive

### Filters

Narrow your results using filters:

- **Location**: Limit to a specific location
- **Owner**: Filter by household member
- **Condition**: Filter items by condition
- **Seasonal**: Filter by season
`,
			no: `
## Søk

StorageHub har kraftig søk som hjelper deg å finne ting raskt.

### Hurtigsøk

Søkefeltet øverst gir umiddelbare resultater:

1. Klikk på søkefeltet
2. Skriv inn søket ditt
3. Resultatene vises mens du skriver
4. Klikk på et resultat for å gå direkte dit

### Søkesiden

For avansert søk, gå til den dedikerte søkesiden:

1. Klikk **Søk** i menyen
2. Skriv inn søkeordene
3. Bruk filtre for å snevre inn resultatene

### Hva du kan søke i

Søket returnerer gjenstander. Søkeordene matcher mot:

- Navn og beskrivelser på gjenstander
- Etiketter og AI-genererte etiketter
- Størrelse
- Hvor gjenstanden er lagret

### Søketips

- Bruk spesifikke ord for bedre resultater
- Søk etter etiketter med etikettnavnet
- Delvise ord fungerer (f.eks. "vin" finner "vinter")
- Søk skiller ikke mellom store og små bokstaver

### Filtre

Snevre inn resultatene med filtre:

- **Sted**: Begrens til ett sted
- **Eier**: Filtrer etter husstandsmedlem
- **Tilstand**: Filtrer gjenstander etter tilstand
- **Sesong**: Filtrer etter sesong
`
		}
	},
	{
		id: 'qr-codes',
		titleKey: 'docs.userGuide.qrCodes.title',
		content: {
			en: `
## QR Codes

QR codes provide quick physical-to-digital access to your containers.

### How It Works

1. Each container has a unique QR code
2. Print and attach the QR code to the physical container
3. Scan the code with your phone to instantly view contents

### Viewing QR Codes

1. Navigate to any container
2. Click the **QR Code** button
3. The QR code displays in a modal

### Printing QR Codes

**Single Label:**
1. View the QR code for a container
2. Click **Print Label**
3. Select your printer and template
4. Print

**Batch Printing:**
1. Go to **God View**
2. Select multiple containers using checkboxes
3. Click **Print Selected**
4. Choose your printer and template
5. Print all labels at once

### Scanning QR Codes

**Using the Mobile App:**
1. Tap **Scan** in the bottom navigation
2. Point your camera at the QR code
3. The container opens automatically

**Using Any QR Scanner:**
- StorageHub QR codes contain URLs
- Any QR scanner will open the container in your browser

### Label Templates

Configure label appearance in printer settings:
- Container name
- QR code size
- Additional information
- Label dimensions

See the Printing Labels section for detailed setup.
`,
			no: `
## QR-koder

QR-koder gir rask tilgang fra fysiske beholdere til den digitale oversikten.

### Hvordan det fungerer

1. Hver beholder har en unik QR-kode
2. Skriv ut og fest QR-koden på den fysiske beholderen
3. Skann koden med telefonen for å se innholdet umiddelbart

### Vise QR-koder

1. Gå til en beholder
2. Klikk **QR-kode**-knappen
3. QR-koden vises i en dialog

### Skrive ut QR-koder

**Enkel etikett:**
1. Vis QR-koden for en beholder
2. Klikk **Skriv ut etikett**
3. Velg skriver og mal
4. Skriv ut

**Flere på en gang:**
1. Gå til **God View**
2. Velg flere beholdere med avkrysningsboksene
3. Klikk **Skriv ut valgte**
4. Velg skriver og mal
5. Skriv ut alle etikettene på én gang

### Skanne QR-koder

**Med mobilappen:**
1. Trykk **Skann** i bunnmenyen
2. Pek kameraet mot QR-koden
3. Beholderen åpnes automatisk

**Med en hvilken som helst QR-skanner:**
- StorageHub-koder inneholder URL-er
- En vanlig QR-skanner åpner beholderen i nettleseren

### Etikettmaler

Konfigurer hvordan etikettene ser ut i skriverinnstillingene:
- Beholdernavn
- QR-kodestørrelse
- Tilleggsinformasjon
- Etikettdimensjoner

Se "Skrive ut etiketter" for detaljert oppsett.
`
		}
	},
	{
		id: 'sharing',
		titleKey: 'docs.userGuide.sharing.title',
		content: {
			en: `
## Sharing

Share containers with others using secure links.

### Creating a Share Link

1. Navigate to a container
2. Click the **Share** button
3. Configure sharing options:
   - **Expiration**: When the link expires (or never)
   - **Allow item view**: Whether items are visible
4. Click **Create Link**
5. Copy and share the link

### Share Link Features

- **Read-only access**: Recipients can view but not edit
- **No login required**: Anyone with the link can view
- **Expiration control**: Set automatic expiration
- **View tracking**: See how many times links are accessed

### Managing Share Links

View and manage active share links:

1. Navigate to the container
2. Click **Share**
3. View active links under "Active Share Links"
4. Delete links you no longer need

### Security Considerations

- Share links grant read access to anyone who has them
- Use expiration dates for temporary sharing
- Delete links when no longer needed
- Shared containers show nested containers and items
- The original URL structure is not exposed
`,
			no: `
## Deling

Del beholdere med andre via sikre lenker.

### Lage en delingslenke

1. Gå til en beholder
2. Klikk **Del**-knappen
3. Konfigurer delingsalternativer:
   - **Utløp**: Når lenken slutter å virke (eller aldri)
   - **Tillat visning av gjenstander**: Om gjenstandene skal vises
4. Klikk **Opprett lenke**
5. Kopier og del lenken

### Funksjoner i delingslenker

- **Skrivebeskyttet**: Mottakere kan se, men ikke redigere
- **Ingen innlogging**: Alle med lenken kan se innholdet
- **Utløpskontroll**: Sett automatisk utløp
- **Sporing**: Se hvor mange ganger lenken er åpnet

### Administrere delingslenker

Vis og administrer aktive lenker:

1. Gå til beholderen
2. Klikk **Del**
3. Se aktive lenker under "Aktive delingslenker"
4. Slett lenker du ikke trenger lenger

### Sikkerhetshensyn

- Delingslenker gir lesetilgang til alle som har dem
- Bruk utløpsdatoer for midlertidig deling
- Slett lenker når de ikke brukes lenger
- Delte beholdere viser også nestede beholdere og gjenstander
- Den opprinnelige URL-strukturen vises ikke
`
		}
	},
	{
		id: 'reminders',
		titleKey: 'docs.userGuide.reminders.title',
		content: {
			en: `
## Reminders

Set reminders to help you manage seasonal items and maintenance tasks.

### Creating a Reminder

1. Navigate to the **Reminders** page
2. Click **Add Reminder**
3. Fill in the details:
   - **Title**: What to remember
   - **Due Date**: When to be reminded
   - **Recurring**: Set up repeat schedule
   - **Link to Item/Container**: Optional association
4. Click **Create**

### Reminder Types

**One-time Reminders:**
- Single occurrence
- Good for specific tasks

**Recurring Reminders:**
- Repeat on a schedule
- Great for seasonal rotations
- Set the interval as "repeat every N days" (e.g. 7 for weekly, 30 for monthly, 365 for yearly)

### Use Cases

- **Seasonal Clothing**: "Switch to winter clothes" (yearly)
- **Maintenance**: "Check smoke detector batteries" (monthly)
- **Rotation**: "Rotate emergency food supplies" (quarterly)
- **Events**: "Pack holiday decorations" (yearly)

### Managing Reminders

**View Reminders:**
- **Pending**: Upcoming reminders
- **Overdue**: Past due reminders
- **Completed**: Finished reminders

**Mark Complete:**
1. Click the checkbox next to a reminder
2. For recurring reminders, the next occurrence is created

**Edit/Delete:**
1. Click on a reminder to view details
2. Use Edit or Delete buttons
`,
			no: `
## Påminnelser

Sett påminnelser for å holde styr på sesongbaserte gjenstander og vedlikehold.

### Opprette en påminnelse

1. Gå til **Påminnelser**-siden
2. Klikk **Legg til påminnelse**
3. Fyll inn detaljene:
   - **Tittel**: Hva som skal huskes
   - **Forfallsdato**: Når du skal bli påminnet
   - **Gjentakende**: Sett opp gjentakelse
   - **Knytt til gjenstand/beholder**: Valgfri kobling
4. Klikk **Opprett**

### Påminnelsestyper

**Engangs:**
- Skjer én gang
- Bra for spesifikke oppgaver

**Gjentakende:**
- Gjentas etter en tidsplan
- Bra for sesongbaserte ting
- Sett intervallet som "gjenta hver N. dag" (f.eks. 7 for ukentlig, 30 for månedlig, 365 for årlig)

### Bruksområder

- **Sesongklær**: "Bytt til vinterklær" (årlig)
- **Vedlikehold**: "Sjekk batterier i røykvarslere" (månedlig)
- **Rotasjon**: "Skift ut nødmatlager" (kvartalsvis)
- **Hendelser**: "Pakk frem juledekorasjoner" (årlig)

### Administrere påminnelser

**Vise påminnelser:**
- **Kommende**: Snart-forfalte påminnelser
- **Forfalt**: Påminnelser som er gått ut
- **Fullført**: Ferdig påminnelser

**Marker som fullført:**
1. Klikk avkrysningsboksen ved siden av en påminnelse
2. For gjentakende påminnelser opprettes neste forekomst automatisk

**Rediger/slett:**
1. Klikk på en påminnelse for å se detaljer
2. Bruk Rediger- eller Slett-knappen
`
		}
	},
	{
		id: 'godview',
		titleKey: 'docs.userGuide.godview.title',
		content: {
			en: `
## God View

God View provides a comprehensive tree view of your entire inventory.

### Accessing God View

Click **God View** in the main navigation.

### Features

**Tree Navigation:**
- Expandable/collapsible tree structure
- Shows all locations, containers, and items
- Click items to expand/collapse
- Visual indicators for container types

**Inline Editing:**
- Click any name to edit it directly
- Press Enter to save, Escape to cancel
- No page navigation required

**Quick Actions:**
- Add containers or items directly from the tree
- Delete items with confirmation
- Move items between containers via drag-and-drop in the tree

### Batch Label Printing

Checkbox selection is used for printing labels in bulk:

1. Click checkboxes to select multiple containers
2. Click **Print Selected**
3. All selected container labels print at once

### Filtering

Use the toolbar filters to narrow the view:
- Search within tree
- Filter by location
- Filter by container type
`,
			no: `
## God View

God View gir deg et komplett trevisning over hele beholdningen din.

### Tilgang til God View

Klikk **God View** i hovedmenyen.

### Funksjoner

**Trenavigasjon:**
- Utvidbar/sammenleggbar trestruktur
- Viser alle steder, beholdere og gjenstander
- Klikk for å åpne/lukke
- Visuelle indikatorer for beholdertyper

**Innebygd redigering:**
- Klikk på et navn for å redigere direkte
- Trykk Enter for å lagre, Escape for å avbryte
- Ingen sidenavigering nødvendig

**Hurtighandlinger:**
- Legg til beholdere eller gjenstander direkte fra treet
- Slett gjenstander med bekreftelse
- Flytt gjenstander mellom beholdere med dra-og-slipp i treet

### Masseutskrift av etiketter

Avkrysningsboksene brukes til å skrive ut etiketter samlet:

1. Klikk avkrysningsboksene for å velge flere beholdere
2. Klikk **Skriv ut valgte**
3. Alle valgte beholderetiketter skrives ut samtidig

### Filtrering

Bruk filtrene i verktøylinjen for å snevre inn:
- Søk i treet
- Filtrer etter sted
- Filtrer etter beholdertype
`
		}
	},
	{
		id: 'outgrown',
		titleKey: 'docs.userGuide.outgrown.title',
		content: {
			en: `
## Outgrown

The **Outgrown** view (top nav, next to God View) surfaces items the
household has aged out of — Sverre's size 92 parka when he's now 5,
Sonja's outgrown shoes — so they don't sit forgotten in storage.

### How items get here

When an item is classified, the AI also estimates an age range for
its size, in months. Children's height-cm clothing sizes and EU
shoe sizes have well-defined mappings (size 92 ≈ 18–24 months,
size 116 ≈ 60–72 months, EU 28 shoes ≈ 48–60 months). Adult sizes
leave the range blank — adult items don't appear here.

The page lists items where the *effective owner's* current age in
months has passed the size's upper bound. The "effective owner" is
the real \`owner_id\` if set, otherwise the AI's suggested owner.

### Inherit-to suggestions

For each outgrown item, the page checks whether another household
member currently fits the size, or will fit within ~12 months. When
a match exists, the row shows a green inherit suggestion:

> → Inherit to Sonja (fits in ~6 months)

- **Reassign** moves the item to the suggested user and removes it
  from the Outgrown view.
- **Dismiss** hides the item from the view (it stays in inventory).
  Dismissed items don't reappear unless their size or the owner's
  age data changes.

Items are grouped by current owner and sorted most-outgrown first.

### Backfilling existing items

Items added before this feature shipped have a \`size\` string but
no age range, so they don't appear here yet. Admins can run
**Admin → AI Settings → Recompute Size Age Ranges** to backfill —
it queues a Celery task that calls a cheap text-only model once per
item. Idempotent; safe to re-run.
`,
			no: `
## Vokst ut

**Vokst ut**-visningen (toppmeny, ved siden av Totaloversikt) viser
ting husstanden har vokst ut av — Sverres størrelse 92-jakke når
han nå er 5, Sonjas utvokste sko — så de ikke blir liggende glemt
på lager.

### Hvordan ting havner her

Når en gjenstand klassifiseres, estimerer AI-en også et
aldersintervall for størrelsen, i måneder. Barneklær med
cm-størrelser og EU-skostørrelser har faste sammenhenger
(str. 92 ≈ 18–24 måneder, str. 116 ≈ 60–72 måneder, EU 28 sko ≈
48–60 måneder). Voksenstørrelser får ingen aldersangivelse — slike
ting vises ikke her.

Siden lister gjenstander der *effektiv eier* har passert
størrelsens øvre grense. "Effektiv eier" er den ekte \`owner_id\`
om satt, ellers AI-ens foreslåtte eier.

### Forslag til arvinger

For hver utvokste gjenstand sjekker siden om et annet familiemedlem
passer størrelsen i dag, eller vil passe innen ~12 måneder. Hvis
det finnes en match, viser raden et grønt forslag:

> → Arve til Sonja (passer om ca. 6 måneder)

- **Tildel på nytt** flytter gjenstanden til foreslått bruker og
  fjerner den fra Vokst ut-listen.
- **Avvis** skjuler gjenstanden fra visningen (den blir værende i
  inventaret). Avviste gjenstander dukker ikke opp igjen med mindre
  størrelse eller eierens alder endres.

Gjenstander grupperes etter nåværende eier og sorteres med mest
utvokste øverst.

### Etterfylle eksisterende gjenstander

Gjenstander lagt til før denne funksjonen kom har en \`size\`-streng
men ingen aldersangivelse, så de vises ikke ennå. Administratorer
kan kjøre **Admin → AI-innstillinger → Beregn aldersintervaller**
for å fylle inn etterpå — det kjører en Celery-jobb som spør en
billig tekstmodell én gang per gjenstand. Idempotent; trygt å
kjøre flere ganger.
`
		}
	},
	{
		id: 'declutter',
		titleKey: 'docs.userGuide.declutter.title',
		content: {
			en: `
## Declutter (Tinder for Items)

The **Declutter** view (top nav, plus the heart icon in the mobile
bottom bar) shows one item at a time and asks for a verdict: 🗑️
**Toss** · 🤔 **Maybe** · ❤️ **Love**. Replaces the bottleneck of
"where do I even start?" with the simpler "what do I keep?".

### The flow

1. Open **/declutter**.
2. Review the current item: image, name, size, owner, container path,
   tags, description.
3. Decide:
   - **Love** — hidden from the deck for 12 months.
   - **Maybe** — comes back in 3 months.
   - **Toss** — moves to the discard pile (no cooldown).
4. The next card loads automatically. A counter at the top shows how
   many items you've reviewed in this session.

Decisions are *shared* per household (one row per item). If your
spouse hits Toss on something you'd keep, you'll see it on the
discard pile and can Undo from there.

### Filtering

A **Filters** toggle in the page header reveals two dropdowns:

- **Owner** — only items owned by this user.
- **Tag** — only items tagged with this tag (top-30 tags by
  eligible-item count).

Use them to focus a session — e.g. "Anders's t-shirts". Combine for
narrower cohorts.

### Mobile swipe gestures

On phones the card responds to swipe gestures:

- **→ Right** = Love
- **← Left** = Toss
- **↑ Up** = Maybe

Visual stamps fade in as you drag past the threshold so you can
preview the decision before releasing. Below the threshold the card
snaps back. The three buttons remain visible for accessibility and
desktop use.

### What's excluded from the deck

- Items currently in cooldown.
- Items already on the discard pile.
- Items with an age range (those live on **Outgrown** instead).
- Items still being AI-processed.

When the deck is exhausted, the page shows "You're all caught up."

### The Discard pile

Click **Discard pile →** to see everything you've marked Toss,
grouped by container path so a single physical sweep handles a whole
shelf.

Per-row actions:

- **Delete** — permanent removal (with confirm).
- **Donated** — soft-delete with a "(donated)" entry in the activity
  log.
- **Undo** — clears the decision; the item returns to the deck.
`,
			no: `
## Rydd (Tinder for ting)

**Rydd**-visningen (toppmeny, og hjerteikonet i mobilens bunnmeny)
viser én gjenstand om gangen og ber om en avgjørelse: 🗑️ **Kast**
· 🤔 **Usikker** · ❤️ **Behold**. Erstatter "hvor skal jeg
begynne?" med "hva vil jeg ha?".

### Slik fungerer det

1. Åpne **/declutter**.
2. Se på gjenstanden: bilde, navn, størrelse, eier, plassering,
   etiketter, beskrivelse.
3. Bestem:
   - **Behold** — skjult fra kortbunken i 12 måneder.
   - **Usikker** — kommer tilbake om 3 måneder.
   - **Kast** — flyttes til kasthaugen (ingen ventetid).
4. Neste kort lastes automatisk. En teller øverst viser hvor mange
   gjenstander du har vurdert i denne økten.

Avgjørelser deles per husstand (én rad per gjenstand). Hvis ektefellen
trykker Kast på noe du ville beholde, ser du det på kasthaugen og
kan angre derfra.

### Filtrering

En **Filtre**-knapp i toppen viser to nedtrekksmenyer:

- **Eier** — kun ting eid av denne brukeren.
- **Etikett** — kun ting med denne etiketten (de 30 mest brukte).

Bruk dem til å fokusere en økt — f.eks. "Anders' t-skjorter".
Kombiner for smalere utvalg.

### Sveipebevegelser på mobil

På telefon reagerer kortet på sveipebevegelser:

- **→ Høyre** = Behold
- **← Venstre** = Kast
- **↑ Opp** = Usikker

Fargede stempler kommer til syne når du drar forbi terskelen, så du
kan se avgjørelsen før du slipper. Under terskelen smeller kortet
tilbake. De tre knappene er alltid synlige for tilgjengelighet og
desktop-bruk.

### Hva er ikke med i kortbunken

- Gjenstander i ventetid.
- Gjenstander allerede på kasthaugen.
- Gjenstander med aldersintervall (de hører til **Vokst ut**).
- Gjenstander som fortsatt blir AI-prosessert.

Når kortbunken er tom viser siden "Du er ferdig for nå."

### Kasthaugen

Klikk **Kasthaugen →** for å se alt du har markert som Kast, gruppert
etter plassering så du kan rydde én hylle av gangen.

Handlinger per rad:

- **Slett** — permanent fjerning (med bekreftelse).
- **Donert** — soft-delete med "(donert)" i aktivitetsloggen.
- **Angre** — fjerner avgjørelsen; gjenstanden går tilbake til kortbunken.
`
		}
	},
	{
		id: 'printing',
		titleKey: 'docs.userGuide.printing.title',
		content: {
			en: `
## Printing Labels

StorageHub supports printing QR code labels to various label printers.

### Supported Printers

**Zebra ZPL Printers:**
- Network-connected Zebra printers
- Uses ZPL (Zebra Programming Language)
- Supports various label sizes

**Brother QL Printers:**
- Brother QL series label printers
- Network or USB connection
- DK label support

**Generic PDF:**
- Outputs PDF files
- Print to any standard printer
- Good for testing

### Setting Up a Printer

1. Navigate to **Printers** page
2. Click **Add Printer**
3. Configure:
   - **Name**: Friendly name for the printer
   - **Type**: Zebra ZPL, Brother QL, or Generic PDF
   - **Connection**: Network address or file path
4. Click **Save**

### Network Printers

For network printers:
1. Ensure printer is on the same network
2. Enter the printer's IP address and port
3. Example: \`192.168.1.100:9100\`

### Test Printing

Always test your printer setup:
1. Navigate to the printer in settings
2. Click **Test Print**
3. Verify the test label prints correctly

### Label Templates

Configure what appears on labels:
- QR code (always included)
- Container name
- Location path
- Custom text

### Troubleshooting

**No output:**
- Verify network connectivity
- Check printer IP address
- Ensure printer is online

**Garbled output:**
- Verify correct printer type selected
- Check label size settings
- Update printer firmware
`,
			no: `
## Skrive ut etiketter

StorageHub støtter utskrift av QR-kodeetiketter til ulike etikettskrivere.

### Støttede skrivere

**Zebra ZPL-skrivere:**
- Nettverkstilkoblede Zebra-skrivere
- Bruker ZPL (Zebra Programming Language)
- Støtter ulike etikettstørrelser

**Brother QL-skrivere:**
- Brother QL-serien
- Nettverk eller USB
- Støtter DK-etiketter

**Generisk PDF:**
- Lager PDF-filer
- Skriv ut til hvilken som helst standard skriver
- Bra for testing

### Sette opp en skriver

1. Gå til **Skrivere**-siden
2. Klikk **Legg til skriver**
3. Konfigurer:
   - **Navn**: Et passende navn
   - **Type**: Zebra ZPL, Brother QL eller Generisk PDF
   - **Tilkobling**: Nettverksadresse eller filsti
4. Klikk **Lagre**

### Nettverksskrivere

For nettverksskrivere:
1. Sørg for at skriveren er på samme nettverk
2. Skriv inn IP-adressen og porten til skriveren
3. Eksempel: \`192.168.1.100:9100\`

### Testutskrift

Test alltid skriveroppsettet:
1. Gå til skriveren i innstillingene
2. Klikk **Testutskrift**
3. Sjekk at testetiketten skrives ut riktig

### Etikettmaler

Konfigurer hva som skal vises på etikettene:
- QR-kode (alltid inkludert)
- Beholdernavn
- Stedssti
- Egendefinert tekst

### Feilsøking

**Ingen utskrift:**
- Sjekk nettverkstilkoblingen
- Sjekk skriverens IP-adresse
- Sørg for at skriveren er online

**Forvridd utskrift:**
- Sjekk at riktig skrivertype er valgt
- Sjekk innstillinger for etikettstørrelse
- Oppdater fastvaren på skriveren
`
		}
	},
	{
		id: 'settings',
		titleKey: 'docs.userGuide.settings.title',
		content: {
			en: `
## Settings

Customize StorageHub to your preferences.

### Accessing Settings

Click your profile picture, then **Settings**.

### Profile

Update your personal information:
- **Name**: Your display name
- **Email**: Contact email (optional)
- **Password**: Set or change your password

### Appearance

**Theme:**
- **Light**: Light background, dark text
- **Dark**: Dark background, light text
- **System**: Follow your device settings

The theme applies immediately throughout the app.

### Language

Choose your preferred language:
- **English**: Full support
- **Norwegian (Norsk)**: Full support

The language setting syncs across all your devices.

### Data Export

Export your data for backup or analysis:

**JSON Export:**
- Complete data export
- Machine-readable format
- Includes all locations, containers, items

**CSV Export:**
- Spreadsheet-compatible format
- Good for reporting and analysis
- A single CSV file listing all items
`,
			no: `
## Innstillinger

Tilpass StorageHub etter dine ønsker.

### Tilgang til innstillinger

Klikk på profilbildet, og deretter **Innstillinger**.

### Profil

Oppdater personlig informasjon:
- **Navn**: Visningsnavnet ditt
- **E-post**: Kontakt-e-post (valgfritt)
- **Passord**: Sett eller endre passord

### Utseende

**Tema:**
- **Lyst**: Lys bakgrunn, mørk tekst
- **Mørkt**: Mørk bakgrunn, lys tekst
- **System**: Følger enhetens innstilling

Temaet brukes umiddelbart i hele appen.

### Språk

Velg foretrukket språk:
- **Engelsk**: Full støtte
- **Norsk**: Full støtte

Språkinnstillingen synkroniseres på alle enhetene dine.

### Dataeksport

Eksporter dataene dine for sikkerhetskopi eller analyse:

**JSON-eksport:**
- Fullstendig dataeksport
- Maskinlesbart format
- Inneholder alle steder, beholdere og gjenstander

**CSV-eksport:**
- Regnearkkompatibelt format
- Bra for rapportering og analyse
- Én CSV-fil med alle gjenstandene
`
		}
	},
	{
		id: 'admin',
		titleKey: 'docs.userGuide.admin.title',
		content: {
			en: `
## Admin Features

Administrators have access to additional management features.

### Accessing Admin Panel

1. Click your profile picture
2. Select **Admin Panel** (only visible to admins)

### User Management

**Creating Users:**
1. Click **Add User**
2. Enter name and optional password
3. Select role (Admin or User)
4. Click **Create**

**Editing Users:**
1. Click on a user
2. Modify details
3. Click **Save**

**Deleting Users:**
1. Click the delete icon
2. Confirm deletion
> Warning: This deletes all user data

### Profile Users

Profiles are household members who own items but never log in — small
kids, pets, anyone you track without giving them an account:

- Create them like regular users and mark them as a profile
- They can be set as item owners and get AI owner suggestions
- They are hidden from the login screen

### Activity Logs

View system-wide activity:
- Who did what and when
- Filter by user or action type
- Useful for auditing

### AI Configuration

Configure AI features:

**Enable/Disable AI:**
- Toggle AI features on or off
- Affects all users

**API Configuration:**
- Set OpenAI API key
- Choose models from a fixed list for image classification and text
  summaries

**Model Selection:**
- GPT-4o: Best quality, recommended for classification
- GPT-4o Mini: Faster, lowest cost

**Usage Statistics:**
- The AI tab shows usage and cost statistics for AI calls

### API Keys

The **API Keys** tab lets you create keys for external integrations:

1. Click **Create Key** and give it a name
2. Choose scopes (read, write, search, webhooks, admin)
3. Copy the key when shown — it starts with \`shub_\` and is only
   displayed once
4. Optionally set an expiration; deactivate keys you no longer use

### Home Assistant Integration

StorageHub can feed inventory data into Home Assistant for sensors,
automations, and voice-activated item search. Create an API key with
\`read\` and \`search\` scopes and follow the setup guide in
\`docs/HOME_ASSISTANT_INTEGRATION.md\` in the repository.

### System Statistics

View overall system metrics:
- Total users
- Total storage items
- AI usage and cost
`,
			no: `
## Admin-funksjoner

Administratorer har tilgang til ekstra administrasjonsfunksjoner.

### Tilgang til adminpanelet

1. Klikk på profilbildet
2. Velg **Adminpanel** (kun synlig for administratorer)

### Brukeradministrasjon

**Opprette brukere:**
1. Klikk **Legg til bruker**
2. Skriv inn navn og valgfritt passord
3. Velg rolle (Admin eller bruker)
4. Klikk **Opprett**

**Redigere brukere:**
1. Klikk på en bruker
2. Endre detaljer
3. Klikk **Lagre**

**Slette brukere:**
1. Klikk slett-ikonet
2. Bekreft slettingen
> Advarsel: Dette sletter alle brukerens data

### Profilbrukere

Profiler er husstandsmedlemmer som eier ting, men som aldri logger inn —
små barn, kjæledyr, eller andre du vil holde oversikt for uten å gi dem
en konto:

- Opprett dem som vanlige brukere og marker dem som profil
- De kan settes som eiere av gjenstander og får AI-eierforslag
- De vises ikke på innloggingsskjermen

### Aktivitetslogger

Se aktivitet på tvers av systemet:
- Hvem gjorde hva og når
- Filtrer etter bruker eller handlingstype
- Nyttig for revisjon

### AI-konfigurasjon

Konfigurer AI-funksjoner:

**Aktivere/deaktivere AI:**
- Slå AI-funksjoner av eller på
- Påvirker alle brukere

**API-konfigurasjon:**
- Sett OpenAI API-nøkkel
- Velg modeller fra en fast liste for bildeklassifisering og
  tekstsammendrag

**Modellvalg:**
- GPT-4o: Best kvalitet, anbefalt for klassifisering
- GPT-4o Mini: Raskere, lavest kostnad

**Bruksstatistikk:**
- AI-fanen viser bruks- og kostnadsstatistikk for AI-kall

### API-nøkler

Fanen **API-nøkler** lar deg opprette nøkler for eksterne integrasjoner:

1. Klikk **Opprett nøkkel** og gi den et navn
2. Velg tilganger (lese, skrive, søk, webhooks, admin)
3. Kopier nøkkelen når den vises — den starter med \`shub_\` og vises
   bare én gang
4. Sett eventuelt en utløpsdato; deaktiver nøkler du ikke bruker lenger

### Home Assistant-integrasjon

StorageHub kan levere inventardata til Home Assistant for sensorer,
automatiseringer og talestyrt gjenstandssøk. Opprett en API-nøkkel med
tilgangene \`read\` og \`search\`, og følg oppsettsguiden i
\`docs/HOME_ASSISTANT_INTEGRATION.md\` i kodearkivet.

### Systemstatistikk

Se overordnede systemmål:
- Totalt antall brukere
- Totalt antall gjenstander
- AI-forbruk og kostnad
`
		}
	},
	{
		id: 'backup',
		titleKey: 'docs.userGuide.backup.title',
		content: {
			en: `
## Backup & Restore

Protect your data with backup features.

### Manual Backup

**Export Data:**
1. Go to **Settings** > **Data**
2. Click **Export as JSON**
3. Save the downloaded file

**Restore Data:**
- Administrators can restore backups from the Admin Panel
- See "Restoring a Backup" below

### Google Drive Integration

Automatically backup to Google Drive:

**Setup (Admin):**
1. Go to **Admin Panel**
2. Navigate to **Google Drive Setup**
3. Upload a Google service-account JSON key and share a Drive folder
   with the service account
4. Configure backup schedule

**Backup Options:**
- **Manual**: Trigger backup on demand
- **Daily**: Automatic daily backup
- **Weekly**: Automatic weekly backup
- **Monthly**: Automatic monthly backup

**What's Backed Up:**
- All locations
- All containers
- All tags
- All items and their image metadata
- All users
- Item photos, only when the backup configuration has "include images"
  enabled

### Restoring a Backup

Administrators restore from **Admin Panel** > **Backups**:

1. Restore directly from an entry in the backup history, or upload a
   backup file
2. Review the preview of what the backup contains
3. Choose whether to restore images
4. Confirm — restoring **merges** the backup into your current data, it
   does not replace it

### Backup Best Practices

1. **Regular Backups**: Set up automatic backups
2. **Multiple Copies**: Keep backups in multiple locations
3. **Test Restores**: Periodically verify backups work
4. **Secure Storage**: Protect backup files

### Data Portability

Your data is yours:
- Export anytime in standard formats
- JSON export is human-readable
- CSV export works with spreadsheets
- No vendor lock-in
`,
			no: `
## Sikkerhetskopi og gjenoppretting

Beskytt dataene dine med sikkerhetskopifunksjoner.

### Manuell sikkerhetskopi

**Eksportere data:**
1. Gå til **Innstillinger** > **Data**
2. Klikk **Eksporter som JSON**
3. Lagre den nedlastede filen

**Gjenopprette data:**
- Administratorer kan gjenopprette sikkerhetskopier fra adminpanelet
- Se "Gjenopprette en sikkerhetskopi" nedenfor

### Google Drive-integrasjon

Sikkerhetskopier automatisk til Google Drive:

**Oppsett (administrator):**
1. Gå til **Adminpanelet**
2. Naviger til **Google Drive-oppsett**
3. Last opp en JSON-nøkkel for en Google-tjenestekonto og del en
   Drive-mappe med tjenestekontoen
4. Konfigurer sikkerhetskopiplan

**Sikkerhetskopialternativer:**
- **Manuelt**: Utløs sikkerhetskopi manuelt
- **Daglig**: Automatisk daglig sikkerhetskopi
- **Ukentlig**: Automatisk ukentlig sikkerhetskopi
- **Månedlig**: Automatisk månedlig sikkerhetskopi

**Hva som tas sikkerhetskopi av:**
- Alle steder
- Alle beholdere
- Alle etiketter
- Alle gjenstander og bildemetadataene deres
- Alle brukere
- Bilder av gjenstander, kun når "inkluder bilder" er slått på i
  sikkerhetskopikonfigurasjonen

### Gjenopprette en sikkerhetskopi

Administratorer gjenoppretter fra **Adminpanelet** > **Sikkerhetskopier**:

1. Gjenopprett direkte fra en oppføring i historikken, eller last opp
   en sikkerhetskopifil
2. Se gjennom forhåndsvisningen av hva kopien inneholder
3. Velg om bilder skal gjenopprettes
4. Bekreft — gjenoppretting **fletter** kopien inn i dataene dine, den
   erstatter dem ikke

### Beste praksis

1. **Regelmessige sikkerhetskopier**: Sett opp automatiske sikkerhetskopier
2. **Flere kopier**: Behold sikkerhetskopier flere steder
3. **Test gjenoppretting**: Verifiser at sikkerhetskopier faktisk fungerer
4. **Sikker lagring**: Beskytt sikkerhetskopifilene

### Dataportabilitet

Dataene er dine:
- Eksporter når du vil i standardformater
- JSON-eksport er lesbar for mennesker
- CSV-eksport fungerer i regneark
- Ingen leverandørbinding
`
		}
	}
];
