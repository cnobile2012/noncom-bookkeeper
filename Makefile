#
# Development by Carl J. Nobile
#
include include.mk

TODAY		= $(shell date +"%Y-%m-%dT%H:%M:%S.%N%:z")
PREFIX		= $(shell pwd)
BASE_DIR	= $(shell echo $${PWD\#\#*/})
TEST_TAG	=
PACKAGE_DIR	= $(BASE_DIR)-$(VERSION)$(TEST_TAG)
APP_NAME	= NC-Bookkeeper
DOCS_DIR	= $(PREFIX)/docs
#LOGS_DIR	= $(PREFIX)/logs
RM_REGEX	= '(^.*.pyc$$)|(^.*.wsgic$$)|(^.*~$$)|(.*\#$$)|(^.*,cover$$)'
RM_CMD		= find $(PREFIX) -regextype posix-egrep -regex $(RM_REGEX) \
                  -exec rm {} \;
COVERAGE_DIR	= $(PREFIX)/.coverage_tests
COVERAGE_FILE	= .coveragerc
COVERAGE_PROCESS_START	= $(COVERAGE_FILE)
TEST_ARGS	= --parallel=4
PIP_ARGS	=

#----------------------------------------------------------------------
all	: tar

#----------------------------------------------------------------------
tar	: clean
	@(cd ..; tar -czvf $(PACKAGE_DIR).tar.gz --exclude=".git" \
          --exclude="__pycache__" $(BASE_DIR))

.PHONY	: tests
tests	: clean
	@rm -rf $(DOCS_DIR)/htmlcov
	@coverage erase --rcfile=$(COVERAGE_FILE)
	@rm -rf $(COVERAGE_DIR)
	@mkdir -p $(COVERAGE_DIR)
	@coverage run --concurrency=multiprocessing \
         --rcfile=$(COVERAGE_FILE)  ./manage.py test $(TEST_ARGS)
	@mv .coverage.* $(COVERAGE_DIR)
	@coverage combine --rcfile=$(COVERAGE_FILE) $(COVERAGE_DIR)
	@coverage report -m --rcfile=$(COVERAGE_FILE)
	@coverage html --rcfile=$(COVERAGE_FILE)
	@echo $(TODAY)

.PHONY	: sphinx
sphinx  : clean
	(cd $(DOCS_DIR); make html)

.PHONY	: install-dev
install-dev:
	pip install $(PIP_ARGS) -r requirements/development.txt

.PHONY	: uninstall-dev
uninstall-dev:
	@rm -rf ${HOME}/.local/share/${APP_NAME}
	@rm -rf ${HOME}/.config/${APP_NAME}
	@rm -rf ${HOME}/.cache/${APP_NAME}

.PHONY	: build-exc
build-exc:
	pyinstaller nc-bookkeeper.py

#----------------------------------------------------------------------
clean	:
	$(shell $(RM_CMD))
	@(cd ${DOCS_DIR}; make clean)

clobber	: clean
	@(cd $(DOCS_DIR); make clobber)
	@rm -rf $(DOCS_DIR)/htmlcov
	@rm -rf build dist *.spec
#	@rm -f $(LOGS_DIR)/*.log*
