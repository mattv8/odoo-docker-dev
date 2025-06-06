#!/bin/bash
set -e

###############################################
# Environment Setup
###############################################

# Binary Paths
PYTHON_BIN="$VENV/bin/python3"
ODOO_BIN="${ODOO_SRC_DIR}/odoo-bin"

# Logging
test -d "${LOG_DIR}" || mkdir -p "${LOG_DIR}"
COLS=$(tput cols 2>/dev/null || echo 150)  # Fallback if tput fails
SEP=$(printf '%*s' "$COLS" '' | tr ' ' '-')

# Export any required environment variables
export INSTALL_THEME=1

###############################################
# Port Allocation (for shell and tests)
###############################################
while true; do
  # Generate a random ephemeral port and its GEVENT partner
  PORT=$(shuf -i 4000-4100 -n 1)
  ((GEVENT_PORT = PORT + 1))

  (echo >/dev/tcp/localhost/$PORT) &>/dev/null && PORT_IN_USE=0 || PORT_IN_USE=1
  (echo >/dev/tcp/localhost/$GEVENT_PORT) &>/dev/null && GEVENT_PORT_IN_USE=0 || GEVENT_PORT_IN_USE=1
  [ $PORT_IN_USE -ne 0 ] && [ $GEVENT_PORT_IN_USE -ne 0 ] && break
done

###############################################
# Helper Functions
###############################################
cleanup_tests() {
  local test_db="$1"
  local logfile="$2"

  if [ -z "$test_db" ] || [ -z "$logfile" ]; then
    echo "Error: Missing required arguments to cleanup_tests"
    return 1
  fi

  printf "%s\n%s\n" "$SEP" "Cleaning up test environment..." | tee -a "$logfile"

  # Brief pause to allow process to exit gracefully
  sleep 1

  echo "Dropping test database ${test_db}." | tee -a "$logfile"
  PGPASSWORD=${DB_PASS} psql -h odoo-postgres -U ${DB_USER} -d postgres -c "DROP DATABASE IF EXISTS \"${test_db}\";" 2>/dev/null || echo "Warning: Could not drop database ${test_db}" | tee -a "$logfile"

  # Check for other ongoing Odoo test processes before resetting PostgreSQL settings
  local test_procs=$(ps aux | grep -v grep | grep '[o]doo-bin.*--test-enable' | grep -o 'testing-[A-Za-z0-9]\{6\}' | grep -v "$test_db" | sort -u | wc -l || echo 0)
  if [ $test_procs -gt 0 ]; then
    echo "Skipping reset PostgreSQL settings because there are $test_procs other test processes running." | tee -a "$logfile"
  else
    echo "No other test processes found. Restoring PostgreSQL settings..." | tee -a "$logfile"
    PGPASSWORD=${DB_PASS} psql -h odoo-postgres -U ${DB_USER} -d postgres -c "ALTER SYSTEM RESET ALL;" 2>/dev/null || echo "Warning: Could not reset PostgreSQL config." | tee -a "$logfile"
    PGPASSWORD=${DB_PASS} psql -h odoo-postgres -U ${DB_USER} -d postgres -c "SELECT pg_reload_conf();" 2>/dev/null || echo "Warning: Could not reload PostgreSQL configuration" | tee -a "$logfile"
  fi

  echo "Cleanup completed." | tee -a "$logfile"
}

parse_extra_args() {
  INSTALL_ALL=0
  USER_TEST_TAGS=""
  ARGS=()

  while [[ $# -gt 0 ]]; do
      case "$1" in
        --install-all|--all)
            INSTALL_ALL=1
            shift
            ;;
        --test-tags|--test-tags=*)
            USER_TEST_TAGS=",${1#*=}"
            shift
            ;;
        *)
        ARGS+=("$1")
        shift
        ;;
      esac
  done
}

###############################################
# Reuseable Odoo Base Commands
###############################################
# Odoo-bin user
RUNAS="su -s /bin/bash odoo -c"

# Only applies to main Odoo service
LIMITS="--limit-time-cpu=3600 --limit-time-real=3600 --max-cron-threads=6"

# Addons path and module upgrade/install flags
ADDONS="/odoo/odoo/addons,/odoo/addons,/odoo-e,/custom-odoo"

# Install any modules listed in .installed_modules file
MODULES=""
if [ -f "${CUSTOM_MODULES_DIR}/.installed_modules" ]; then
  MODULE_LIST=$(awk 'NF && $1!~/^#/{printf "%s,",$1}' ${CUSTOM_MODULES_DIR}/.installed_modules | sed 's/,$//')
  [ -n "$MODULE_LIST" ] && MODULES="-i ${MODULE_LIST}"
fi

# SMTP settings (using Mailpit)
SMTP_SETTINGS="--smtp=mailpit --smtp-port=1025"

CMD_BASE="-r ${DB_USER} -w ${DB_PASS} --log-level=${LOG_LEVEL} \
  --db_host=odoo-postgres --db_port=5432 --data-dir=${DATA_DIR} ${SMTP_SETTINGS} \
  --addons-path=${ADDONS}"

###############################################
# ODOO Shell
###############################################
if [ "$1" = "shell" ]; then
  echo "Entering Odoo shell..."
  FINAL_CMD="${PYTHON_BIN} ${ODOO_BIN} shell ${CMD_BASE} -p ${PORT} -d ${DB_NAME} \
    --gevent-port=${GEVENT_PORT} ${MODULES} ${@:2}"
  printf "%s\nCommand: %s\n%s\n" "$SEP" "$(echo "${FINAL_CMD}" | sed -e 's/[[:space:]]\+/ /g')" "$SEP"
  exec bash -c "${FINAL_CMD}"
  exit 0

###############################################
# ODOO Tests
###############################################
elif [ "$1" = "test" ] || [ "$1" = "tests" ]; then

  # Excluded test tags (based on exclusions from Odoo.sh)
  EXCLUDED_TESTS="--test-tags=-/website/tests/test_website_form_editor.py:TestWebsiteFormEditor.test_tour,-:TestMailingUi.test_mass_mailing_code_view_tour,-:TestStockLandedCostsLots.test_stock_landed_costs_lots,-/website/tests/test_automatic_editor.py:TestAutomaticEditor.test_01_automatic_editor_on_new_website,-:TestWebsiteFormEditor.test_tour,-:TestWebsitePageProperties.test_website_page_properties_can_publish,-:TestUi.test_website_sale_renting_comparison_ui,-.test_website_sale_subscription_product_variant_add_to_cart,-:TestWebsiteFormEditor.test_tour,-/survey/tests/test_survey_ui_session.py:TestUiSession.test_admin_survey_session,-:TestMailgateway.test_message_process_references_multi_parent_notflat,-:TestUiHtmlEditor.test_html_editor_scss,-:TestActivityPerformance.test_generic_activities_misc_batch,-/website/tests/test_snippets.py:TestSnippets.test_03_snippets_all_drag_and_drop,-/test_mail/tests/test_mail_push.py:TestWebPushNotification.test_notify_by_push_mail_gateway,-:TestIndustryFsmUi.test_ui,-/website_event_booth_exhibitor/tests/test_wevent_booth_exhibitor.py:TestWEventBoothExhibitorCommon.test_register,-:TestPushNotification.test_push_notifications_mail_replay,-/web/tests/test_favorite.py:TestFavorite.test_favorite_management,-:TestUi.test_15_website_link_tools,-:TestWebsiteSaleProductPage.test_toggle_contact_us_button_visibility,-/test_mail_enterprise/tests/test_activity_performance.py:TestActivityPerformance.test_voip_activities_misc_batch,-/website/tests/test_snippets.py:TestSnippets.test_snippet_image_gallery_reorder,-:TestStudioUIUnit.test_form_view_not_altered_by_studio_xml_edition,-/test_mail_full/tests/test_mail_performance.py:TestPortalFormatPerformance.test_portal_message_format_monorecord,-:TestIrMailServerSMTPD,-/pos_self_order/tests/test_self_order_kiosk.py:TestSelfOrderKiosk.test_self_order_kiosk,-/sale_subscription/tests/test_subscription_controller.py:TestSubscriptionController.test_automatic_invoice_token,-:TestSystray.test_05_not_reditor_not_tester,-/website/tests/test_snippets.py:TestSnippets.test_snippet_popup_with_scrollbar_and_animations,-/knowledge/tests/test_knowledge_editor_commands.py:TestKnowledgeEditorCommands.test_knowledge_article_commands_tour,-/website/tests/test_website_form_editor.py:TestWebsiteFormEditor.test_website_form_conditional_required_checkboxes,-/knowledge/tests/test_knowledge_editor_commands.py:TestKnowledgeEditorCommands.test_knowledge_calendar_command_tour,-/website_sale/tests/test_website_sale_image.py:TestWebsiteSaleRemoveImage.test_website_sale_add_and_remove_main_product_image_no_variant,-/website_sale/tests/test_website_sale_image.py:TestWebsiteSaleRemoveImage.test_website_sale_remove_main_product_image_with_variant,-/pos_restaurant_preparation_display/tests/test_frontend.py:TestUi.test_02_preparation_display_resto,-/pos_restaurant_preparation_display/tests/test_frontend.py:TestUi.test_payment_does_not_cancel_display_orders,-/crm/tests/test_crm_ui.py:TestUi.test_01_crm_tour,-/l10n_mx_edi_pos/tests/test_tour.py:TestUi.test_settle_account_mx,-:TestUi.test_snippet_background_video,-/pos_settle_due/tests/test_frontend.py:TestPoSSettleDueHttpCommon.test_pos_reconcile,-/website_sale_collect/tests/test_click_and_collect_flow.py:TestClickAndCollectFlow.test_buy_with_click_and_collect_as_public_user,-/l10n_es_edi_tbai/tests/test_17_5_tbai_document.py:TestEdiDocumentToTbaiDocument,-:TestWebsitePageProperties.test_website_page_properties_website_page,-/stock_barcode_mrp/tests/test_barcode_mrp_production.py:TestMRPBarcodeClientAction.test_barcode_production_add_byproduct,-/website_payment/tests/test_snippets.py:TestSnippets.test_01_donation,-:TestSelfOrderKiosk.test_self_order_language_changes,-:TestIrSequenceGenerate.test_ir_sequence_iso_directives"

  TEST_DB="testing-$(tr -dc A-Za-z0-9 </dev/urandom | head -c 6)"
  LOGFILE="${LOG_DIR}/${TEST_DB}.log"

  # Set test-friendly PostgreSQL settings
  echo "Configuring PostgreSQL for testing..." | tee -a "$LOGFILE"
  PGPASSWORD=${DB_PASS} psql -h odoo-postgres -U ${DB_USER} -d postgres -c "ALTER SYSTEM SET lock_timeout = 0;" || echo "Warning: Could not set lock_timeout" | tee -a "$LOGFILE"
  PGPASSWORD=${DB_PASS} psql -h odoo-postgres -U ${DB_USER} -d postgres -c "ALTER SYSTEM SET statement_timeout = 0;" || echo "Warning: Could not set statement_timeout" | tee -a "$LOGFILE"
  PGPASSWORD=${DB_PASS} psql -h odoo-postgres -U ${DB_USER} -d postgres -c "ALTER SYSTEM SET idle_in_transaction_session_timeout = 1800000;" || echo "Warning: Could not set idle_in_transaction_session_timeout" | tee -a "$LOGFILE"
  PGPASSWORD=${DB_PASS} psql -h odoo-postgres -U ${DB_USER} -d postgres -c "SELECT pg_reload_conf();" || echo "Warning: Could not reload PostgreSQL configuration" | tee -a "$LOGFILE"

  echo "Starting Odoo tests..." | tee -a "$LOGFILE"

  # If no arguments or '--install-all' is provided, auto-install all modules from /custom-odoo;
  # otherwise, use the modules specified in .installed_modules.
  shift  # Remove 'test' or 'tests' from the arguments

  # Parse any extra arguments
  parse_extra_args "$@"

  # Auto-install modules if --install-all is present
  if [ $INSTALL_ALL -eq 1 ]; then
    echo "Auto-installing modules from /custom-odoo" | tee -a "$LOGFILE"
    # Get sorted modules (excluding top dir and hidden dirs)
    MODULE_LIST=$(find /custom-odoo -mindepth 1 -maxdepth 1 -type d ! -name '.*' -printf '%f\n' | sort -V | tr '\n' ',' | sed 's/,$//')
    TEST_MODULES="-i ${MODULE_LIST}"
  else
    TEST_MODULES="${MODULES}"
  fi

  # Build the testing command
  CMD="${PYTHON_BIN} ${ODOO_BIN} ${CMD_BASE} -d ${TEST_DB} --test-enable \
    --http-port=${PORT} --gevent-port=${GEVENT_PORT} --max-cron-threads=0 --stop-after-init \
    ${EXCLUDED_TESTS}${USER_TEST_TAGS} ${TEST_MODULES} ${ARGS[@]}"
  FINAL_CMD="${RUNAS} \"SUPPRESS_FS_ERR=0 INSTALL_THEME=0 ${CMD}\""

  printf "%s\nCommand: %s\n%s\n" "$SEP" "$(echo "${FINAL_CMD}" | sed -e 's/[[:space:]]\+/ /g')" "$SEP" | tee -a "$LOGFILE"

  trap "cleanup_tests '$TEST_DB' '$LOGFILE'" EXIT

  # Log results of the test (using unbuffer for colored tty output)
  unbuffer bash -c "${FINAL_CMD}" 2>&1 | tee >(ansifilter -r -a >> "$LOGFILE")

  if [ $? -eq 0 ]; then
    echo "Test completed successfully." | tee -a "$LOGFILE"
  else
    echo "Test encountered errors." | tee -a "$LOGFILE"
  fi
  exit 0

###############################################
# ODOO Neutralize
###############################################
elif [ "$1" = "neutralize" ]; then
  echo "Running Odoo neutralize..."
  CMD="${PYTHON_BIN} ${ODOO_BIN} neutralize ${CMD_BASE} -d ${DB_NAME} ${@:2}"
  FINAL_CMD="${RUNAS} \"${CMD}\""
  printf "%s\nCommand: %s\n%s\n" "$SEP" "$(echo "${FINAL_CMD}" | sed -e 's/[[:space:]]\+/ /g')" "$SEP"
  exec bash -c "${FINAL_CMD}"

###############################################
# ODOO Scaffold
###############################################
elif [ "$1" = "scaffold" ]; then
  echo "Running Odoo scaffold..."
  shift  # Remove 'scaffold' from the arguments

  # Extract module name (first argument) and optional template
  MODULE_NAME="$1"
  shift

  if [ -z "$MODULE_NAME" ]; then
    echo "Error: Module name is required for scaffold command" >&2
    exit 1
  fi

  # Force scaffold to always use /custom-odoo as destination
  CMD="${PYTHON_BIN} ${ODOO_BIN} scaffold ${MODULE_NAME} /custom-odoo ${@}"
  FINAL_CMD="${RUNAS} \"${CMD}\""
  printf "%s\nCommand: %s\n%s\n" "$SEP" "$(echo "${FINAL_CMD}" | sed -e 's/[[:space:]]\+/ /g')" "$SEP"
  exec bash -c "${FINAL_CMD}"

###############################################
# Upgrade or Install Modules
###############################################
elif [ "$1" = "-u" ] || [ "$1" = "-i" ]; then
  FLAG="$1"
  ACTION=$([ "$1" = "-u" ] && echo upgrade || echo install)
  echo "Performing module ${ACTION}..."
  shift  # Remove the flag from the arguments

  # Parse any extra arguments
  parse_extra_args "$@"

  # If --install-all was passed, auto-discover modules from /custom-odoo.
  # Optionally, append any explicitly passed module names.
  if [ $INSTALL_ALL -eq 1 ]; then
    echo "Auto ${ACTION}ing all modules from /custom-odoo..."
    MODULE_LIST=$(find /custom-odoo -mindepth 1 -maxdepth 1 -type d ! -name '.*' -printf '%f\n' | sort -V | tr '\n' ',' | sed 's/,$//')
    if [ ${#ARGS[@]} -gt 0 ]; then
      MODULES="${MODULE_LIST},$(IFS=,; echo "${ARGS[*]}")"
    else
      MODULES="${MODULE_LIST}"
    fi
  else
    MODULES="$(IFS=,; echo "${ARGS[*]}")"
  fi

  CMD="${PYTHON_BIN} ${ODOO_BIN} ${CMD_BASE} -d ${DB_NAME} --stop-after-init ${FLAG} ${MODULES}"
  FINAL_CMD="${RUNAS} \"${CMD}\""
  printf "%s\nCommand: %s\n%s\n" "$SEP" "$(echo "${FINAL_CMD}" | sed -e 's/[[:space:]]\+/ /g')" "$SEP"
  exec bash -c "${FINAL_CMD}"

###############################################
# Start or Restart Odoo Normally
###############################################
elif [ "$1" = "restart" ] || [ "$#" -eq 0 ]; then
  CMD="${PYTHON_BIN} -m debugpy --listen 0.0.0.0:5678 ${ODOO_BIN} ${CMD_BASE} ${LIMITS} -d ${DB_NAME} ${SMTP_SETTINGS} ${MODULES} ${@:2}"
  FINAL_CMD="${RUNAS} \"${CMD}\""
  PID_FILE="/tmp/odoo.pid"

  if [ "$1" = "restart" ]; then
    if [ -f "$PID_FILE" ]; then
      OLD_PID=$(cat "$PID_FILE")
      if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Stopping Odoo service (PID: $OLD_PID)..."
        kill -SIGTERM "$OLD_PID"
        while kill -0 "$OLD_PID" 2>/dev/null; do
          sleep 0.1 # Wait for process to exit
        done
        echo "Odoo service stopped."
        rm -f "$PID_FILE"  # Remove PID file regardless
      fi
    fi
  fi

  echo "Starting Odoo server..."
  printf "%s\nCommand: %s\n%s\n" "$SEP" "$(echo "${FINAL_CMD}" | sed -e 's/[[:space:]]\+/ /g')" "$SEP"
  exec bash -c "${FINAL_CMD}" &
  NEW_PID=$!
  echo "$NEW_PID" > "$PID_FILE"

  tail -f /dev/null

###############################################
# Unrecognized Argument
###############################################
else
  echo "Error: unrecognized argument '$1'" >&2
  exit 1
fi
