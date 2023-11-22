#
# Development by Carl J. Nobile
#
# The 'logo' and 'icons' target requires povray and imagemagick to be
# installed.
#
include include.mk

TODAY		= $(shell date +"%Y-%m-%dT%H:%M:%S.%N%:z")
PREFIX		= $(shell pwd)
BASE_DIR	= $(shell echo $${PWD\#\#*/})
TEST_TAG	=
PACKAGE_DIR	= $(BASE_DIR)-$(VERSION)$(TEST_TAG)
APP_NAME	= NC-Bookkeeper
DOCS_DIR	= $(PREFIX)/docs
LOGS_DIR	= $(PREFIX)/logs
BUILD_PKG_DIR	= $(PREFIX)/package
RM_REGEX	= '(^.*.pyc$$)|(^.*.wsgic$$)|(^.*~$$)|(.*\#$$)|(^.*,cover$$)'
RM_CMD		= find $(PREFIX) -regextype posix-egrep -regex $(RM_REGEX) \
                  -exec rm {} \;
TEST_TAG	=
PIP_ARGS	= # Pass var for pip install.
TEST_PATH	=

#----------------------------------------------------------------------
all	: tar

#----------------------------------------------------------------------
tar	: clean
	@(cd ..; tar -czvf $(PACKAGE_DIR).tar.gz --exclude=".git" \
          --exclude="__pycache__" $(BASE_DIR))

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

.PHONY	: build-exc
build-spec:
	pyinstaller nc-bookkeeper.spec

#----------------------------------------------------------------------
clean	:
	$(shell $(RM_CMD))
	@(cd ${DOCS_DIR}; make clean)

clobber	: clean
	@(cd $(DOCS_DIR); make clobber)
	@rm -rf build dist
	@rm -rf $(LOGS_DIR)
	@rm -rf $(BUILD_PKG_DIR)
