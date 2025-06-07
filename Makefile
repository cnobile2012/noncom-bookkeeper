#
# Development by Carl J. Nobile
#
# NOTES:
# 1. The 'logo' and 'icons' target requires povray and imagemagick to be
#    installed.
# 2. To build Linux packages the ruby gem fpm needs to be installed.
#    sudo apt install ruby
#    sudo add-apt-repository universe
#    sudo apt install rpm rpm2cpio alien
#    gem install fpm --user-install
#    Then put `.local/share/gem/ruby/<version>/bin in $PATH.
#    Logout then login again.
#
include include.mk

TODAY		= $(shell date +"%Y-%m-%dT%H:%M:%S.%N%:z")
PREFIX		= $(shell pwd)
BASE_DIR	= $(shell basename $(PREFIX))
PACKAGE_DIR	= $(BASE_DIR)-$(VERSION)$(TEST_TAG)
APP_NAME	= nc-bookkeeper
DOCS_DIR	= $(PREFIX)/docs
LOGS_DIR	= $(PREFIX)/logs
BUILD_PKG_DIR	= $(PREFIX)/package
RM_REGEX	= '(^.*.pyc$$)|(^.*.wsgic$$)|(^.*~$$)|(.*\#$$)|(^.*,cover$$)'
RM_CMD		= find $(PREFIX) -regextype posix-egrep -regex $(RM_REGEX) \
                  -exec rm {} \;
COVERAGE_FILE	= $(PREFIX)/.coveragerc
PIP_ARGS	= # Pass variables for pip install.
TEST_PATH	= # The path to run tests on.
TEST_TAG	= # Define the rc<version>

#----------------------------------------------------------------------
.PHONY	: all
all	: help

#----------------------------------------------------------------------
.PHONY: help
help	:
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : \
                2>/dev/null | awk -v RS= \
                -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data \
                     base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep \
                -E -v -e '^[^[:alnum:]]' -e '^$@$$'

.PHONY	: tar
tar	: clobber
	@(cd ..; tar -czvf $(PACKAGE_DIR).tar.gz --exclude=".git" \
          --exclude="__pycache__" --exclude=".pytest_cache" $(BASE_DIR))

# Run all tests
# $ make tests
#
# Run all tests in a specific test file.
# $ make tests TEST_PATH=tests/test_bases.py
#
# Run all tests in a specific test file and class.
# $ make tests TEST_PATH=tests/test_bases.py::TestBases
#
# Run just one test in a specific test file and class.
# $ make tests TEST_PATH=tests/test_bases.py::TestBases::test_version
.PHONY	: tests
tests	: clobber
	@rm -rf $(DOCS_DIR)/htmlcov
	@mkdir -p $(LOGS_DIR)
	@coverage erase --rcfile=$(COVERAGE_FILE)
	@coverage run --rcfile=$(COVERAGE_FILE) -m pytest --capture=tee-sys \
         --ignore tests/individual $(TEST_PATH)
	@coverage report -m --rcfile=$(COVERAGE_FILE)
	@coverage html --rcfile=$(COVERAGE_FILE)
	@echo $(TODAY)

.PHONY  : flake8
flake8  :
        # Error on syntax errors or undefined names.
	flake8 . --select=E9,F7,F63,F82 --show-source
        # Warn on everything else.
	flake8 . --exit-zero

# --------------------------------------------------------------------

.PHONY	: sphinx
sphinx  : clean
	(cd $(DOCS_DIR); make html)

.PHONY  : latexpdf
latexpdf:
	(cd $(DOCS_DIR); make latexpdf)

.PHONY	: epub
epub	:
	(cd $(DOCS_DIR); make epub)

.PHONY	: alldocs
alldocs	: sphinx epub latexpdf

# --- Install and uninstall environments -----------------------------

.PHONY	: install-dev
install-dev:
	pip install $(PIP_ARGS) -r requirements/development.txt \
            --log logs/pip.log

.PHONY	: uninstall-dev
uninstall-dev:
	@rm -rf ${PREFIX}/data

.PHONY	: uninstall-prod
uninstall-prod:
	@rm -rf ${HOME}/.local/share/${APP_NAME}
	@rm -rf ${HOME}/.config/${APP_NAME}
	@rm -rf ${HOME}/.cache/${APP_NAME}

# --- Build final executables ----------------------------------------

.PHONY	: logo
logo	:
	povray +w1280 +h1280 +p +x +d0 -v -icontrib/icon/logo.pov

.PHONY	: icons
icons	:
	convert $(PREFIX)/contrib/icon/logo.png -resize 48x48 \
                $(PREFIX)/images/bookkeeper-48x48.ico
	convert $(PREFIX)/contrib/icon/logo.png -resize 72x72 \
                $(PREFIX)/images/bookkeeper-72x72.png
	convert $(PREFIX)/contrib/icon/logo.png -resize 64x64 \
                $(PREFIX)/images/bookkeeper-64x64.png
	convert $(PREFIX)/contrib/icon/logo.png -resize 48x48 \
                $(PREFIX)/images/bookkeeper-48x48.png
	convert $(PREFIX)/contrib/icon/logo.png -resize 32x32 \
                $(PREFIX)/images/bookkeeper-32x32.png
	convert $(PREFIX)/contrib/icon/logo.png -resize 24x24 \
                $(PREFIX)/images/bookkeeper-24x24.png
	convert $(PREFIX)/contrib/icon/logo.png -resize 16x16 \
                $(PREFIX)/images/bookkeeper-16x16.png

.PHONY	: images
images	:
	@cp $(PREFIX)/contrib/images/*-30x36.bmp $(PREFIX)/images/

# To add a pre-release candidate such as 'rc1' to a test package name an
# environment variable needs to be set that setup.py can read.
#
# The command below will work with any package target below.
# make build-deb TEST_TAG=rc1
#
# For example a deb file might look like 'nc-bookkeeper-0.10rc1-amd64.deb'.
#
# Steps to build packages.
# 1. make build-all
# or
# 1. make build-spec
# 2. make package
# 3. make build-deb or make build-rpm
#
.PHONY	: build-spec
build-spec:
	@pyinstaller nc-bookkeeper.spec

.PHONY	: package
package	:
	./scripts/package.py

.PHONY	: build-all
build-all: clobber build-spec package build-deb build-rpm

.PHONY	: build-deb
build-deb:
	@fpm -C package -s dir -t deb -n $(APP_NAME) -v $(VERSION)$(TEST_TAG) \
             --license MIT -p build/$(APP_NAME)-$(VERSION)$(TEST_TAG)-amd64.deb

.PHONY	: build-rpm
build-rpm:
	@fpm -C package -s dir -t rpm -n $(APP_NAME) -v $(VERSION)$(TEST_TAG) \
             --license MIT -p build/$(APP_NAME)-$(VERSION)$(TEST_TAG)-amd64.rpm

#----------------------------------------------------------------------
.PHONY	: clean clobber

clean	:
	$(shell $(RM_CMD))

clobber	: clean
#	@(cd $(DOCS_DIR); make clobber)
	@rm -rf build dist
	@rm -rf $(LOGS_DIR)
	@rm -rf $(BUILD_PKG_DIR)
	@rm -rf $(DOCS_DIR)/htmlcov
