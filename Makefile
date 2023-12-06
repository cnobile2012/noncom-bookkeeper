#
# Development by Carl J. Nobile
#
# NOTES:
# 1. The 'logo' and 'icons' target requires povray and imagemagick to be
#    installed.
# 2. To build Linux packages the ruby gem fpm needs to be installed.
#    sudo apt-get install ruby
#    gem install fpm --user-install
#
include include.mk

TODAY		= $(shell date +"%Y-%m-%dT%H:%M:%S.%N%:z")
PREFIX		= $(shell pwd)
BASE_DIR	= $(shell echo $${PWD\#\#*/})
TEST_TAG	= # Define the rc<version>
PACKAGE_DIR	= $(BASE_DIR)-$(VERSION)$(TEST_TAG)
APP_NAME	= nc-bookkeeper
DOCS_DIR	= $(PREFIX)/docs
LOGS_DIR	= $(PREFIX)/logs
BUILD_PKG_DIR	= $(PREFIX)/package
RM_REGEX	= '(^.*.pyc$$)|(^.*.wsgic$$)|(^.*~$$)|(.*\#$$)|(^.*,cover$$)'
RM_CMD		= find $(PREFIX) -regextype posix-egrep -regex $(RM_REGEX) \
                  -exec rm {} \;
PIP_ARGS	= # Pass variables for pip install.
TEST_PATH	= # The path to run tests on.

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
          --exclude="__pycache__" $(BASE_DIR))

# $ make tests
# $ make tests TEST_PATH=tests.test_bases
# $ make tests TEST_PATH=tests/test_bases.py:TestBases.test_version
.PHONY	: tests
tests	: clobber
	@mkdir -p $(LOGS_DIR)
	@nosetests --with-coverage --cover-erase --cover-inclusive \
                   --cover-html --cover-html-dir=$(DOCS_DIR)/htmlcov \
                   --cover-package=$(PREFIX)/src $(TEST_PATH)
	@echo $(TODAY)

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

.PHONY	: build-spec
build-spec:
	@pyinstaller nc-bookkeeper.spec

.PHONY	: package
package	:
	./scripts/package.py

# To add a pre-release candidate such as 'rc1' to a test package name an
# environment variable needs to be set that setup.py can read.
#
# The command below will work with any package target below.
# make build-deb TEST_TAG=rc1
#
# For example a deb file might look like 'nc-bookkeeper-0.10rc1-amd64.deb'.
#
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
	@(cd ${DOCS_DIR}; make clean)
	$(shell $(RM_CMD))

clobber	: clean
	@(cd $(DOCS_DIR); make clobber)
	@rm -rf build dist
	@rm -rf $(LOGS_DIR)
	@rm -rf $(BUILD_PKG_DIR)
