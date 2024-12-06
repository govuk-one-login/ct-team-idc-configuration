#!/bin/bash

START_COMMIT=$1
END_COMMIT=$2

FILES_CHANGED=$(git diff --name-only ${START_COMMIT} ${END_COMMIT})

NEW_POLICIES=()

verify_vpc_config() {
  file=$1
  if grep -q "AWS::Lambda::Function" "$file"; then
    if ! grep -q "VpcConfig" "$file"; then
      echo "File fails checks: $file"
      echo "Add a VpcConfig block from a template such as amplify/backend/function/teamAccounts/teamgetAccounts-cloudformation-template.json"
    fi
  fi
}

verify_new_aws_api_endpoints() {
  file=$1
  if grep -q "AWS::Lambda::Function" "$file"; then
    POLICIES=$(jq -r '.Resources[] | select(.Type=="AWS::IAM::Policy") | .Properties.PolicyDocument.Statement[].Action[]' $file | cut -d ':' -f 1)
    echo "New lambda endpoints to check: $file"
    for policy in ${POLICIES[@]}:
    do
      NEW_POLICIES+=($(echo $policy | cut -d ':' -f 1))
    done
  fi
}

# verify_schema_changes() {
#   file=$1
#   if git diff $START_COMMIT $END_COMMIT -- "$file"; then
#   fi
# }

for file in ${FILES_CHANGED[@]}:
do
  case $file in
    amplify/backend/**/*-template.json)
      verify_new_aws_api_endpoints "$file"
      verify_vpc_config "$file"
      ;;
    # src/models/schema.js)
    #   verify_schema_changes "$file"
    #   ;;
  esac
done

NEW_POLICIES=(`printf '%s\n' "${NEW_POLICIES[@]}" | sort | uniq`)

echo "AWS API endpoints used by new lambdas: ${NEW_POLICIES[*]}"
