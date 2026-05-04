#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INIT_SQL_PATH="${PROJECT_DIR}/sql/init.sql"
ENV_PATH="${PROJECT_DIR}/.env"
MAKE_DOTENV=false

usage() {
  echo "Usage: $0 [--make-dotenv]"
}

dotenv_escape() {
  local value="$1"
  value="${value//\'/\'\"\'\"\'}"
  printf "'%s'" "${value}"
}

upsert_env_var() {
  local key="$1"
  local value="$2"
  local file_path="$3"
  local escaped_value

  escaped_value="$(dotenv_escape "${value}")"

  if [[ -n "$(sed -n "/^${key}=/p" "${file_path}" | sed -n '1p')" ]]; then
    sed -i '' -E "s|^${key}=.*$|${key}=${escaped_value}|" "${file_path}"
  else
    printf "%s=%s\n" "${key}" "${escaped_value}" >> "${file_path}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --make-dotenv)
      MAKE_DOTENV=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Option inconnue: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v gum >/dev/null 2>&1; then
  echo "Erreur: gum n'est pas installe. Voir https://github.com/charmbracelet/gum" >&2
  exit 1
fi

if ! command -v mysql >/dev/null 2>&1; then
  gum style --foreground 196 "Erreur: le client mysql n'est pas installe."
  exit 1
fi

if [[ ! -f "${INIT_SQL_PATH}" ]]; then
  gum style --foreground 196 "Erreur: fichier introuvable: ${INIT_SQL_PATH}"
  exit 1
fi

gum style --bold --foreground 212 "Configuration MySQL"
gum style "Ce script configure la connexion puis execute: source sql/init.sql"

MYSQL_HOST="$(gum input --placeholder "Host MySQL" --value "127.0.0.1")"
MYSQL_PORT="$(gum input --placeholder "Port MySQL" --value "3306")"
MYSQL_USER="$(gum input --placeholder "Utilisateur MySQL" --value "root")"
MYSQL_PASSWORD="$(gum input --password --placeholder "Mot de passe MySQL (laisser vide si aucun)")"
MYSQL_DB="$(gum input --placeholder "Nom de la base cible (info)" --value "jdr")"
INIT_SQL_DB="$(
  sed -nE 's/^[[:space:]]*[Cc][Rr][Ee][Aa][Tt][Ee][[:space:]]+[Dd][Aa][Tt][Aa][Bb][Aa][Ss][Ee]([[:space:]]+IF[[:space:]]+NOT[[:space:]]+EXISTS)?[[:space:]]+`?([A-Za-z0-9_]+)`?[[:space:]]*;.*/\2/p' "${INIT_SQL_PATH}" | sed -n '1p'
)"

if [[ -z "${MYSQL_HOST}" || -z "${MYSQL_PORT}" || -z "${MYSQL_USER}" ]]; then
  gum style --foreground 196 "Erreur: host, port et utilisateur sont obligatoires."
  exit 1
fi

if ! [[ "${MYSQL_PORT}" =~ ^[0-9]+$ ]]; then
  gum style --foreground 196 "Erreur: le port doit etre numerique."
  exit 1
fi

if [[ -n "${INIT_SQL_DB}" && "${MYSQL_DB}" != "${INIT_SQL_DB}" ]]; then
  gum style --foreground 214 "Attention: la base saisie (${MYSQL_DB}) differe de celle du script SQL (${INIT_SQL_DB})."
  if ! gum confirm "Continuer quand meme avec l'import de ${INIT_SQL_PATH} ?"; then
    gum style --foreground 196 "Operation annulee."
    exit 1
  fi
elif [[ -z "${INIT_SQL_DB}" ]]; then
  gum style --foreground 214 "Attention: impossible de detecter la base dans ${INIT_SQL_PATH}."
fi

if [[ "${MAKE_DOTENV}" == true ]]; then
  touch "${ENV_PATH}"
  upsert_env_var "MYSQL_HOST" "${MYSQL_HOST}" "${ENV_PATH}"
  upsert_env_var "MYSQL_PORT" "${MYSQL_PORT}" "${ENV_PATH}"
  upsert_env_var "MYSQL_USER" "${MYSQL_USER}" "${ENV_PATH}"
  upsert_env_var "MYSQL_PASSWORD" "${MYSQL_PASSWORD}" "${ENV_PATH}"
  upsert_env_var "MYSQL_DB" "${MYSQL_DB}" "${ENV_PATH}"
  gum style --foreground 42 ".env mis a jour: ${ENV_PATH}"
fi

gum style --foreground 244 "Test de connexion a ${MYSQL_HOST}:${MYSQL_PORT} avec l'utilisateur ${MYSQL_USER}..."

MYSQL_ARGS=(
  --host="${MYSQL_HOST}"
  --port="${MYSQL_PORT}"
  --user="${MYSQL_USER}"
)

if [[ -n "${MYSQL_PASSWORD}" ]]; then
  if MYSQL_PWD="${MYSQL_PASSWORD}" mysql "${MYSQL_ARGS[@]}" --execute="SELECT 1;" >/dev/null 2>&1; then
    gum style --foreground 42 "Connexion OK"
  else
    gum style --foreground 196 "Connexion KO. Verifie tes identifiants et l'accessibilite du serveur."
    exit 1
  fi
else
  if mysql "${MYSQL_ARGS[@]}" --execute="SELECT 1;" >/dev/null 2>&1; then
    gum style --foreground 42 "Connexion OK"
  else
    gum style --foreground 196 "Connexion KO. Verifie tes identifiants et l'accessibilite du serveur."
    exit 1
  fi
fi

gum style --foreground 244 "Base cible indiquee: ${MYSQL_DB}"
gum style --foreground 244 "Import de ${INIT_SQL_PATH}..."

if [[ -n "${MYSQL_PASSWORD}" ]]; then
  MYSQL_PWD="${MYSQL_PASSWORD}" mysql "${MYSQL_ARGS[@]}" < "${INIT_SQL_PATH}"
else
  mysql "${MYSQL_ARGS[@]}" < "${INIT_SQL_PATH}"
fi

gum style --foreground 42 --bold "Setup termine avec succes."
