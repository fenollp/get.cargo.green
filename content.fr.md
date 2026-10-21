# cargo.green landing page, in French

Same format, sections and items as content.md, which documents them.
Keep `install` tab names and `#anchors` as they are in content.md.

## meta
title: cargo green ~ Des builds Rust qui ne partent jamais de zéro
description: cargo-green met en cache chaque crate Rust que vous compilez et le partage avec votre équipe et votre CI, via BuildKit ou Nix et un registre que vous utilisez déjà. Mêmes commandes cargo, un mot de plus.
og_title: cargo green ~ Des builds Rust qui ne partent jamais de zéro
og_description: Cache de build par crate pour Rust, partagé entre postes de travail et CI. Basé sur BuildKit ou Nix et n'importe quel registre OCI.
url: https://cargo.green
repo: https://github.com/fenollp/supergreen
sales_email: sales@cargo.green
copyright: © 2026 cargo.green · CLI sous licence AGPL-3.0

## nav
cta: Essai gratuit | #pricing
links:
  - Pourquoi | #problem
  - Installer | #use-install
  - Fonctionnement | #how
  - Configuration | #config
  - Entreprise | #enterprise
  - Tarifs | #pricing

## hero
badge: Open source · Granularité maximale · Stockage au choix | #how
headline: Des builds Rust qui ne partent jamais {à froid}
cta_primary: Installer la CLI | #use-install
cta_secondary: Contacter les ventes | #enterprise
repo_label: cargo green install --frozen cargo-nextest
caption: Exécution réelle, CARGO_TARGET_DIR vide

Compilez chaque crate une seule fois. Ensuite, chaque poste et chaque job de CI le télécharge au
lieu de le recompiler. Mêmes commandes `cargo`, un mot de plus : `cargo green build`. Démarrez avec
le cache mondial gratuit, ou gardez tout dans votre propre registre.

### Granularité du cache
value: Par crate

### Construit avec
value: Nix ou BuildKit

### Stockage du cache
value: Tout registre OCI

## registries
label: Fonctionne avec le registre que vous utilisez déjà
items:
  - GCR
  - GHCR
  - ECR
  - Nix cache
  - S3
  - R2

## problem
heading: Votre équipe recompile les mêmes dépendances toute la journée.

Le `target/` de votre poste ne sert qu'à vous. Vos collègues et la CI recompilent les mêmes
`serde`, `tokio` et des centaines d'autres crates sur chaque machine, chaque branche et chaque pull
request. Cela coûte des minutes par build et une facture de CI pour compiler du code que personne
n'a modifié.

### Les caches locaux restent locaux
icon: hard-drive

`target/` appartient à une seule machine. Un nouveau clone, un nouveau worktree ou un nouveau runner
de CI repart de zéro.

### Les caches partagés ratent
icon: unplug

Les outils qui copient des fichiers compilés d'une machine à l'autre ratent dès que les chemins, les
toolchains ou les bibliothèques système diffèrent.

### Les caches de CI, c'est tout ou rien
icon: archive-restore

La plupart des caches de CI stockent une seule archive indexée sur `Cargo.lock`. Mettez à jour une
dépendance et tout le cache est perdu.

## answer
heading: Un cache par crate, identique sur chaque machine.
kicker: Compilez une fois. Réutilisez partout.
points:
  - Modifiez un crate, recompilez un crate (et ce qui en dépend)
  - Le cache sert sur les postes, les runners de CI et les serveurs de build
  - Couvre les proc-macros, les build scripts et l'édition de liens
  - Compilez sur une machine distante via SSH
  - Toujours `cargo` : aucun nouveau système de build à apprendre

`cargo green` compile chaque crate dans un environnement isolé et figé, avec BuildKit ou Nix. Le
même crate obtient la même clé de cache sur chaque machine, si bien que le build d'un collègue ou un
job de CI peut réutiliser le vôtre. Les résultats sont stockés dans un registre que vous contrôlez.

## ci
heading: Une CI plus rapide dès le premier job.

Pas de préchauffage ni de correspondance de lockfile. Le premier job sur un cache partagé saute
chaque crate que quelqu'un a déjà compilé.

### Indépendant de Cargo.lock
icon: unlink

Mettez à jour une dépendance : seuls ce crate et ceux qui en dépendent sont recompilés.

### Téléchargé pendant le build
icon: download-cloud

Les crates en cache se téléchargent pendant la compilation. Aucune étape de restauration ne bloque
le job.

### Aucune étape de cache
icon: scissors

Retirez les actions de sauvegarde et de restauration du cache de votre workflow. Rien à archiver,
envoyer ou faire expirer.

## install
heading: Une installation. Un mot de plus.
link: Documentation d'installation complète | https://github.com/fenollp/supergreen#installation
default_tab: build

`cargo green` est un plugin cargo. Vos commandes, votre `Cargo.toml` et votre CI ne changent pas.

### install

```sh
# Depuis crates.io
cargo install cargo-green

# …ou suivez la dernière version depuis git
cargo install --locked --force \
  --git https://github.com/fenollp/supergreen.git cargo-green

# Vérifiez que $CARGO_HOME/bin est dans votre $PATH
which cargo-green

# Il faut un moteur de build sur la machine pour écrire dans le cache :
#   un client docker ou podman, ou nix.
```

### build

```sh
# Une fois : repartir de zéro
cargo clean

# Puis utilisez cargo, avec un mot de plus
cargo green build
cargo green test
cargo green clippy

# Ça vous plaît ? Rendez-le invisible
alias cargo='cargo green'

# Choisissez votre moteur : docker (par défaut), podman ou nix
export CARGOGREEN_RUNNER=nix

# Un simple `cargo build` fonctionne toujours ensuite.
```

### remote

```sh
# Compilez sur la machine à 96 cœurs, exécutez le binaire en local
DOCKER_HOST=ssh://build-farm-01 cargo green test

# Même idée avec le moteur Nix
CARGOGREEN_RUNNER=nix NIX_SSHOPTS="-A" \
  cargo green build --release

# Les portables restent silencieux. Les ventilateurs aussi.
```

### share cache

```toml
# Cargo.toml
[package.metadata.green]
cache-images = [
  "docker-image://ghcr.io/acme/payments-api",
]
cache-from-images = [
  "docker-image://ghcr.io/acme/global-cache",
]

# Publiez le cache pour tous les autres
cargo green supergreen push
```

### CI

```yaml
# .github/workflows/ci.yml
- run: cargo install cargo-green
- run: cargo green test
  env:
    CARGOGREEN_CACHE_IMAGES: docker-image://ghcr.io/acme/api

# Préchauffez le cache pour les runners hors ligne / isolés
- run: cargo green supergreen sync
```

## commands
heading: Commandes supplémentaires

Toutes sous `cargo green supergreen`.

### cargo green supergreen setup
<!--desc: Crée les liens symboliques nécessaires-->

### cargo green supergreen env
desc: Affiche les réglages utilisés

### cargo green supergreen doc
desc: Explique chaque réglage

### cargo green supergreen sync
desc: Télécharge tout pour compiler hors ligne

<!--### cargo green supergreen push-->
<!--desc: Publie le cache partagé, tous les tags-->

### cargo green supergreen builder
desc: Gère le builder local ou distant

<!--### cargo green supergreen show-rust-base-->
<!--desc: Affiche l'environnement de build utilisé-->

## how
heading: Envelopper, traduire, compiler, partager.

`cargo green` se branche sur `$RUSTC_WRAPPER`, un point d'extension que `cargo` prend déjà en
charge. Quatre étapes s'exécutent entre `cargo green build` et votre binaire.

### Envelopper
icon: git-fork

`cargo green` définit `$RUSTC_WRAPPER` et lance `cargo`. `cargo` résout et ordonnance toujours votre build.

### Traduire
icon: file-code-2

Chaque appel à `rustc` et chaque build script devient une étape de build isolée, figée sur votre toolchain exacte.

### Compiler
icon: cpu

[Nix](https://nixos.org/) ou [BuildKit](https://github.com/moby/buildkit) ([Docker](https://docs.docker.com/build/buildkit/), [Podman](https://podman.io/)) exécute les étapes en parallèle, en local ou sur une machine distante.

### Mettre en cache et partager
icon: database-zap

Le résultat de chaque crate est récupéré depuis le stockage ou envoyé vers celui-ci. Vous, votre équipe, la CI et le monde entier partagez un seul cache.

## hits
icon: lock
heading: Pourquoi le cache sert aussi sur les autres machines
points:
  - L'environnement de build est figé, pas emprunté à l'hôte
  - Les chemins sont normalisés : votre `$HOME` n'entre jamais dans une clé de cache
  - Les dépendances git sont figées sur une révision exacte
  - Les sorties sont reproductibles, jusqu'aux horodatages des fichiers
footnote: En prime : *les builds sont auditables*. Vous pouvez montrer ce qui a produit un binaire et le recompiler plus tard pour le prouver.

Deux machines qui compilent le même crate produisent en général des clés différentes. `cargo green` élimine les différences :

## engines
icon: split
heading: Deux moteurs, un seul workflow
footnote: Les portables n'ont pas besoin de faire tourner un démon. Pointez `cargo green` vers une machine partagée et c'est elle qui compile.

Utilisez le moteur que votre équipe a déjà. Les commandes, la configuration et les résultats en cache sont les mêmes avec les deux.

### BuildKit
icon: container
config: runner = "docker" | "podman"

Utilise votre client `docker` ou `podman`. Le cache vit dans n'importe quel registre OCI.

### Nix
icon: hexagon
config: runner = "nix"

Pour les équipes sous `nix`. Le cache vit dans un cache binaire Nix, toujours par crate.

## config
heading: Fonctionne par défaut. Configurable au besoin.
link: Référence complète | https://github.com/fenollp/supergreen#configuration
reference_title: Chaque option, documentée
reference_body: Chaque réglage est documenté avec sa valeur par défaut, un exemple et sa variable d'environnement.
reference_cta: Lire la référence de configuration
reference_href: https://github.com/fenollp/supergreen#configuration

Définissez les options dans `[package.metadata.green]` de `Cargo.toml`, ou avec les variables
d'environnement `$CARGOGREEN_*`. Les variables d'environnement sont prioritaires, ce qui convient à
la CI.

### Cache et partage
icon: database
href: https://github.com/fenollp/supergreen#caching
chips:
  - cache-images
  - cache-from-images
  - cache-to-images
  - registry-mirrors

Où les crates en cache sont lus et écrits, pour que votre équipe, les forks et la CI partagent un seul cache.

### Moteur de build
icon: split
href: https://github.com/fenollp/supergreen#cargogreen_runner
chips:
  - runner
  - $DOCKER_HOST
  - $BUILDX_BUILDER

Quel moteur compile (`docker`, `podman` ou Nix) et sur quelle machine.

### Environnement de build
icon: box
href: https://github.com/fenollp/supergreen#cargogreen_base_image
chips:
  - base-image
  - with-network
  - components
  - add.apt
  - add.apk

Avec quoi chaque crate est compilé : image de base, paquets système, composants de la toolchain, accès réseau.

### Diagnostic
icon: scroll-text
href: https://github.com/fenollp/supergreen#cargogreen_log
chips:
  - $CARGOGREEN_LOG
  - $CARGOGREEN_LOG_PATH
  - supergreen env

Les journaux, et les réglages exacts utilisés par `cargo green`, pour quand un build vous surprend.

### Artefacts et provenance
icon: file-output
href: https://github.com/fenollp/supergreen#cargogreen_final_path
chips:
  - final-path

Exportez la définition du build en un seul fichier à archiver, relire ou recompiler ailleurs. Réutilisable pour construire des images OCI.

## enterprise
heading: Votre cache reste sur votre infrastructure.
cta: Planifier une revue de sécurité | #pricing

Le cache n'a besoin d'aucun serveur [cargo.green](https://cargo.green). C'est du contenu ordinaire
dans votre registre ou votre cache binaire : il peut vivre dans votre compte cloud, votre VPC ou un
réseau isolé.

### SOC 2 Type II (prévu)
icon: shield-check

Pas encore certifié. Audit prévu ; DPA et clauses contractuelles types pour les données de l'UE sur
demande.

### SSO, SCIM et jetons à portée limitée
icon: key-round

Connexion SAML et OIDC, groupes synchronisés avec l'annuaire, jetons de lecture/écriture par projet
avec rotation.

### BYOC et réseau isolé
icon: cloud-cog

Utilisez votre propre compte cloud et votre registre, en mono-locataire, ou synchronisez le cache
dans un réseau sans accès à Internet.

### SLA de disponibilité et support direct (prévu)
icon: activity

Un engagement de disponibilité écrit, un ingénieur support attitré et un canal Slack partagé sont
sur la feuille de route. Aujourd'hui, parlez directement aux mainteneurs.

### Journaux d'audit et attribution
icon: file-search

Qui a compilé quoi, quand, depuis quelle révision, et quelles équipes génèrent les dépenses de build.

### Cœur open source
icon: scale

La CLI est sous AGPL-3.0 : vous pouvez auditer chaque ligne. Plan de contrôle auto-hébergé et
licence commerciale disponibles si l'AGPL ne vous convient pas.

## pricing
heading: La CLI est gratuite, pour toujours.
note: Tarif par organisation, pas par siège : les jobs de CI et les agents de code compilent aussi.
discount: −20 %
footnote: Les limites sont souples. Un mois chargé ne cassera pas votre build ; nous vous contacterons si cela devient la norme.

Notre cache public mondial est gratuit : tout le monde peut le lire, et les utilisateurs connectés
peuvent y écrire. Votre propre registre OCI ne coûte rien non plus. Vous ne payez que pour un cache
privé, hébergé par nous ou sur site, facturé à l'usage par organisation.

### Développeur
blurb: Particuliers, projets perso, open source.
price: 0 $
period: gratuit pour toujours
cta: Installer la CLI | #use-install
features:
  - Cache mondial : lectures gratuites, sans compte
  - Écritures gratuites une fois connecté
  - {20 Go} de stockage de cache
  - {500 k} requêtes / mois
  - Projets et sièges illimités
  - Rétention de 7 jours
  - Statistiques de build : ce qui est lent, ce qui a raté
  - Support communautaire sur GitHub

### Équipe
blurb: Startups qui livrent du Rust tous les jours.
price: 49 $
price_annual: 39 $
period: / mois
sub: Par organisation
badge: Le plus populaire
featured: true
cta: Essai gratuit de 14 jours | #
features:
  - Tout le forfait Développeur, plus :
  - {500 Go} de stockage de cache
  - {10 millions} de requêtes / mois
  - 200 heures-cœur de builds distants
  - Dépassement à 0,15 $/Go, 0,10 $/heure-cœur
  - Cache privé pour le code privé
  - Rétention de 30 jours
  - Support prioritaire par e-mail, sous 1 jour ouvré

### Scale
blurb: Organisations de 20 à 100 développeurs.
price: 400 $
price_annual: 320 $
period: / mois
sub: Par organisation
cta: Essai gratuit de 14 jours | #
features:
  - Tout le forfait Équipe, plus :
  - {2 To} de stockage de cache
  - {100 millions} de requêtes / mois
  - 2 000 heures-cœur de builds distants
  - Runners préchauffés : les pull requests ne partent jamais à froid
  - Attribution des dépenses par équipe et par dépôt
  - Rétention de 90 jours, configurable par projet
  - Canal Slack partagé (prévu)

### Entreprise
blurb: Équipes plateforme et sécurité avec leurs propres règles.
price: Sur mesure
sub: Contrat annuel, paiement sur facture
cta: Nous contacter | mailto:sales@cargo.green
features:
  - Tout le forfait Scale, plus :
  - Requêtes, stockage et calcul sur mesure
  - Plan de contrôle auto-hébergé, BYOC ou réseau isolé
  - SSO/SAML, SCIM, export des journaux d'audit
  - DPA et revue de sécurité
  - SOC 2 Type II et SLA de 99,9 % (prévus)
  - Ingénieur support dédié (prévu)
  - Licence commerciale et influence sur la feuille de route

## table
heading: Comparer les forfaits
columns:
  - Développeur
  - Équipe
  - Scale
  - Entreprise
rows:
  - CLI cargo-green (AGPL-3.0) | Illimitée | Illimitée | Illimitée | Illimitée
  - Moteurs BuildKit et Nix | yes | yes | yes | yes
  - Votre propre registre | yes | yes | yes | yes
  - Requêtes de cache / mois | 500 k | {10 M} | {100 M} | Sur mesure
  - Stockage du cache | 20 Go | {500 Go} | {2 To} | Sur mesure
  - Heures-cœur de builds distants | no | 200 | 2 000 | Sur mesure
  - Rétention | 7 jours | 30 jours | 90 jours | Sur mesure
  - Projets / sièges | Illimités | Illimités | Illimités | Illimités
  - Cache de crates préchauffé | yes | yes | yes | yes
  - Statistiques de build | yes | yes | yes | yes
  - Attribution des dépenses | no | no | yes | yes
  - SSO/SAML et SCIM | no | no | no | yes
  - Auto-hébergé / réseau isolé | no | no | no | yes
  - SLA de disponibilité | no | no | no | Prévu
  - Support | Communauté | E-mail prioritaire | E-mail + Slack (prévu) | Ingénieur dédié (prévu)

## faq
heading: Questions fréquentes

### Dois-je changer ma façon de travailler ?

Non. Lancez `cargo clean` une fois, puis utilisez `cargo green build` comme `cargo build`. Les
fichiers produits sont les mêmes. Un simple `cargo build` fonctionne toujours : vous pouvez arrêter
quand vous voulez.

### Est-ce que cela nous enferme ?

Non. La CLI est open source (AGPL-3.0) et le cache est du contenu ordinaire dans le registre de
votre choix. Changez de registre avec une ligne de configuration.

### Faut-il Docker sur chaque poste de développeur ?

Non. Pour lire le cache public, aucun moteur n'est nécessaire. Pour compiler, il faut un client
`docker` ou `podman`, ou Nix, et la compilation peut se faire sur une machine distante partagée
plutôt que sur le portable.

### Quelle différence avec sccache ou cargo-chef ?

`sccache` exige des chemins et des environnements identiques d'une machine à l'autre, ne sait pas
mettre en cache l'édition de liens, peine avec les proc-macros, et avec un backend distant la
vérification du cache peut prendre plus de temps que la compilation. `cargo-chef` met en cache
toutes les dépendances dans une seule couche Docker : une mise à jour les recompile toutes.
cargo-green compile chaque crate dans une étape isolée et figée : les clés correspondent d'une
machine à l'autre, le cache est par crate, et une correspondance partielle fait quand même gagner
du temps. Voir la [comparaison](https://github.com/fenollp/supergreen#alternatives) complète dans
le README.

### BuildKit ou Nix ?

Celui que vous utilisez déjà. La plupart des équipes ont docker ou podman, c'est donc le choix par
défaut. Sous Nix, utilisez Nix et gardez votre cache binaire. Les commandes, la configuration et les
résultats sont les mêmes, et les deux peuvent partager le cache.

### En combien de temps la CI devient-elle plus rapide ?

Dès le premier job. Les crates en cache se téléchargent pendant le build plutôt que dans une étape
de restauration préalable. Une branche qui met à jour une dépendance réutilise tout le reste.

### Peut-on compiler sans accès réseau ?

Oui. `cargo green supergreen sync` télécharge à l'avance toutes les images et tous les crates ; les
builds n'ont ensuite plus besoin du réseau. Les environnements isolés sont pris en charge avec le
forfait Entreprise.

### Qu'est-ce qui est gratuit ?

La lecture du cache public mondial : aucun compte nécessaire. L'écriture : gratuite une fois
connecté. L'utilisation de votre propre registre : toujours gratuite. Les forfaits payants couvrent
un cache privé, hébergé par nous ou sur site.

### Qu'est-ce qu'une requête de cache ?

Une lecture ou une écriture d'un crate en cache. Un build à chaud d'un workspace de 400 crates
représente environ 400 requêtes : 10 millions suffisent donc aux postes et à la CI d'une équipe
active. La consommation apparaît dans le tableau de bord avant d'apparaître sur une facture.

### Où est le code source ?

Sur [GitHub](https://github.com/fenollp/supergreen), sous AGPL-3.0. Les issues et pull requests
sont les bienvenues.

## cta
heading: Arrêtez de payer deux fois pour le même build.
command: cargo install cargo-green
button: Contacter les ventes | mailto:sales@cargo.green

Installez la CLI, puis ajoutez `green` à votre prochaine commande cargo.

## footer
tagline: Un builder pour Rust, avec cache et prêt pour l'exécution distante. Fait partie du projet [supergreen](https://github.com/fenollp/supergreen).
status: Tous les systèmes sont opérationnels
disclaimer: cargo green est un projet indépendant. Il n'est ni affilié à la Rust Foundation ou au Rust Project, ni approuvé ou parrainé par eux. Rust et Cargo sont des marques de la Rust Foundation, citées ici uniquement pour décrire la compatibilité.
legal:
  - Confidentialité | #
  - Conditions | #
  - DPA | #

### Produit
links:
  - Pourquoi cargo-green | #problem
  - Installer | #use-install
  - Fonctionnement | #how
  - Tarifs | #pricing

### Docs
links:
  - Configuration | https://github.com/fenollp/supergreen#configuration
  - Exécution distante | https://github.com/fenollp/supergreen#remote-execution
  - Cache | https://github.com/fenollp/supergreen#caching
  - Alternatives | https://github.com/fenollp/supergreen#alternatives

### Entreprise
links:
  - GitHub | https://github.com/fenollp/supergreen
  - Contacter les ventes | mailto:sales@cargo.green
  - Sécurité | #enterprise
  - Statut | #

## ui
skip: Aller au contenu
theme_label: Basculer entre thème clair et sombre
theme_title: Changer de thème
language: Langue
baseline: cargo install classique :
restored: Restaurés
hit_rate: Taux de succès
wall_clock: Durée réelle
tabs_label: Utiliser cargo-green
copy: Copier
copied: Copié
copy_command: Copier la commande d'installation
monthly: Mensuel
annual: Annuel
annual_label: Passer à la facturation annuelle
billed_yearly: , facturé annuellement
