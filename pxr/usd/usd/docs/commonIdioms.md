# Common Idioms and Examples {#Usd_Page_CommonIdioms}

## Traversing a Stage {#Usd_StageTraversal}

The Usd API provides a number of methods for fast, configurable
traversal of a stage or sub-trees of prims on a stage.  The two categories
of traversal are recursion and iteration.  Common to both is the ability
to specify a "predicate" that governs which prims will actually be yielded
by the API during a traversal, and which will be skipped.  Predicates are
conjunctions, disjunctions, and negations of a set of tests of core properties
of UsdPrim that are cached for speedy access during stage population.  See
\ref Usd_PrimFlags "Prim Flags" for more detail and examples.

### Traversing with Recursion {#Usd_StageTraversal_Recursion}

UsdPrim provides a number of methods for accessing its direct children via
a "range", with which one can construct very efficient recursive functions.
The standard UsdPrim::GetChildren() uses the "canonical traversal predicate,"
which implies all active, loaded, defined, non-abstract children.
UsdPrim::GetFilteredChildren() allows specification of a custom predicate.

### Traversing with Iteration {#Usd_StageTraversal_Ieration}

UsdPrim::GetDescendants() returns a range for all of a prim's "canonical"
decendants, and UsdPrim::GetFilteredDescendants() allows the range's
predicate to be specified.

UsdPrimRange enables highly customized iterations, adding the ability
to perform pre-and-post-order traversals, and to prune subtrees.  
The convenience method UsdStage::Traverse() returns a UsdPrimRange
that visits all descendants of the pseudo-root, but not the
pseudo-root itself.

## Working With Schema Classes {#Usd_WorkingWithSchemas}

Later we'll talk about how to create new schema classes...

### Create vs Get Property Methods {#Usd_Create_Or_Get_Property}

For a UsdAttribute named "points" defined in a schema class, you will
find two access methods in the schema class in C++ and python:
\li GetPointsAttr()
\li CreatePointsAttr()

What is the difference between these two methods, and when should you use
each?  GetPointsAttr() simply returns a UsdAttribute object, without authoring
any scene description.  It is therefore threadsafe, and it should be your
choice in any code that may be executed in a multithreaded, "multiple readers"
section. Of course, the UsdAttribute it returns has an API that includes 
mutating methods that \b will author scene description, and those methods
should be avoided in multi-threaded sections.  However, there is no guarantee
that the UsdAttribute returned by GetPointsAttr() will be \em valid for use
in authoring scene description, because there may not be any definition 
available for the attribute in the Stage's scene description, which means
(for example) the Set() method might not know what the attribute's datatype
is.  CreatePointsAttr(), by contrast, will actually create a typed
definition for the attribute in the current UsdEditTarget if no definition
for the attribute yet exists - it follows that it is legal and safe to 
call CreatePointsAttr() even if the attribute is already defined in the
current UsdEditTarget().

In general, you should use CreateXXXAttr() when authoring scene description,
and GetXXXAttr() when reading/importing scene description.  CreateXXXAttr() 
also allows you to specify a default value to assign to the attribute, which
you can specify to author sparsely, which means that we will refrain from
authoring the provided value iff:
\li there is currently no authored value for the attribute on the composed
prim
\li the attribute has a fallback value on the composed prim, and the fallback
value matches the provided value.  If the prim has no composed typeName (i.e. in
the authoring context, the prim is a pure override), then \em no attribute on
the prim will possess a fallback, since fallbacks apply via the prim's typeName.

The same pattern holds for relationships, except that CreateXXXRel() does not
allow specification of a default target, because relationships are 
\em list-edited, and it would be unclear whether to \em add or \em set the
target when there are already authored target opinions.

\note <b>USDeeper: Schema Registry of IsA Schemas.</b> \em IsA schemas are
registered in the \ref UsdSchemaRegistry, which provides automatic (also
directly queryable) access to the typed definition of each property listed in
a schema's definition in its originating schema.usda file.  The properties
defined in each \em IsA schema are called "builtins", which means they are
considered present on prims of that type even when unauthored, and builtin
attributes can be provided a \em fallback value that will be returned by
UsdAttribute::Get() when the attribute possesses no authored scene
description.  Therefore, when authoring builtin properties on a defined,
typed prim, one is technically not required to use the CreateXXXAttr()
method, because the core consults the schema registry using the prim typeName
and the property name to define the property, if no definition has yet been
authored.  Note also that when querying the typeName of a builtin, UsdAttribute
will always consult only the property definition in the schema registry, even
if one has attempted to change the attribute's type in a stringer layer.
However, \em HasA schemas record no typename on prims, nor are
they present in the schema registry. So one \em must use CreateXXXAttr() when
authoring scene description using \em HasA schemas. CreateXXXAttr() is also
useful with \em IsA schemas for authoring onto an untyped, "pure override"
prim that the author knows will later compose onto a typed prim of a
compatible schema type (though of course, care should be exercised).
However, code that consistently uses CreateXXXAttr() for authoring will be
easier to maintain since it will help distinguish reader sections from
writer sections.

## Bool Return Values and Safe Operator Bool {#Usd_BoolReturns}

## Error Reporting Policy and Control {#Usd_ErrorReporting}
